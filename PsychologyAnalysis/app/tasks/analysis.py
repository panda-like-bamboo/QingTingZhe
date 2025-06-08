# app/tasks/analysis.py
import logging
import os
import sys
import asyncio
import json
# --- 使用异步和同步 Redis 客户端 ---
import redis.asyncio as aredis # 异步别名
import redis # 标准同步客户端

# --- 路径设置 (保持不变) ---
TASK_DIR = os.path.dirname(os.path.abspath(__file__))
APP_ROOT_FROM_TASK = os.path.dirname(TASK_DIR) # app/
PROJECT_ROOT_FROM_TASK = os.path.dirname(APP_ROOT_FROM_TASK) # PsychologyAnalysis/
if PROJECT_ROOT_FROM_TASK not in sys.path:
    sys.path.insert(0, PROJECT_ROOT_FROM_TASK)
    print(f"[Celery Task Init] 已添加 {PROJECT_ROOT_FROM_TASK} 到 sys.path 以供 worker 使用")

# --- 核心导入 (添加 STATUS_PENDING, STATUS_PROCESSING) ---
try:
    from app.core.celery_app import celery_app
    from app.core.config import settings
    from app.db.session import AsyncSessionLocal
    from app.crud import assessment as crud_assessment
    # +++ 导入所有需要的状态常量 +++
    from app.models.assessment import STATUS_COMPLETE, STATUS_FAILED, STATUS_PENDING, STATUS_PROCESSING
    # +++++++++++++++++++++++++++++++
    from src.ai_utils import generate_report_content
    from src.utils import setup_logging
    WORKER_LOGGER_NAME = f"{settings.APP_NAME}_Worker"
    setup_logging(log_level_str=settings.LOG_LEVEL,
                    log_dir_name=os.path.basename(settings.LOGS_DIR),
                    logger_name=WORKER_LOGGER_NAME)
    logger = logging.getLogger(WORKER_LOGGER_NAME)
    print(f"[Celery Task Init] Logger '{WORKER_LOGGER_NAME}' 配置完成。")
except ImportError as e:
        print(f"[Celery Task Init] CRITICAL: 无法导入 src 模块或状态常量: {e}", exc_info=True)
        generate_report_content = None
        # --- 添加后备定义 ---
        STATUS_COMPLETE = "complete"
        STATUS_FAILED = "failed"
        STATUS_PENDING = "pending"
        STATUS_PROCESSING = "processing"
        # ---------------------
        logger = logging.getLogger(__name__)
        if not logger.hasHandlers(): logging.basicConfig(level=logging.INFO)
        logger.critical(f"CRITICAL: 核心处理函数 (generate_report_content) 或状态常量导入失败: {e}")
except Exception as setup_err:
        print(f"[Celery Task Init] CRITICAL: 初始化失败: {setup_err}", exc_info=True)
        generate_report_content = None
        # --- 添加后备定义 ---
        STATUS_COMPLETE = "complete"
        STATUS_FAILED = "failed"
        STATUS_PENDING = "pending"
        STATUS_PROCESSING = "processing"
        # ---------------------
        logger = logging.getLogger(__name__)
        if not logger.hasHandlers(): logging.basicConfig(level=logging.INFO)
        logger.critical(f"CRITICAL: 初始化失败: {setup_err}")

# --- Redis Publish Function (保持不变) ---
def publish_report_status_sync(assessment_id: int, status: str, error_msg: str = None):
    """同步地将报告状态发布到 Redis。"""
    global logger
    if not hasattr(settings, 'REDIS_URL'):
         logger.error(f"Worker (Sync): settings 对象缺少 REDIS_URL，无法发布 ID {assessment_id} 的状态 '{status}'。")
         return
    channel_name = f"report-ready:{assessment_id}"
    message_payload = {"status": status}
    if error_msg:
        message_payload["error"] = error_msg
    message_json = json.dumps(message_payload)
    redis_client = None
    try:
        redis_client = redis.Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True
        )
        redis_client.publish(channel_name, message_json)
        logger.info(f"Worker (Sync): 已向频道 '{channel_name}' 发布消息: {message_json}")
    except Exception as e:
        logger.error(f"Worker (Sync): 向频道 '{channel_name}' 发布消息时出错: {e}", exc_info=True)
    finally:
         if redis_client:
              try:
                   redis_client.close()
                   logger.debug(f"Worker (Sync): Redis client for publish ID {assessment_id} closed.")
              except Exception as close_err:
                   logger.warning(f"Worker (Sync): 关闭 Redis publish client 时出错: {close_err}")

# --- Celery 任务定义 (更新 global 声明) ---
@celery_app.task(bind=True, name='tasks.run_ai_analysis')
def run_ai_analysis(self, assessment_id: int):
    """
    Celery 任务：异步运行 AI 分析、更新报告文本和状态，完成后 *同步* 发布 Redis 消息。
    """
    # +++ 确保所有使用的状态常量都在 global 声明中 +++
    global logger, STATUS_COMPLETE, STATUS_FAILED, STATUS_PENDING, STATUS_PROCESSING
    # +++++++++++++++++++++++++++++++++++++++++++++++
    if logger is None:
        print("CRITICAL ERROR: Logger 在 run_ai_analysis 任务中不可用!")
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)

    task_id_str = f"[Celery Task {self.request.id}]"
    logger.info(f"{task_id_str} 收到任务，评估 ID: {assessment_id}")

    if generate_report_content is None:
        error_msg = "核心处理函数导入失败"
        logger.error(f"{task_id_str} {error_msg}，中止任务 ID {assessment_id}。")
        try:
            async def update_fail_status():
                async with AsyncSessionLocal() as session:
                    # 使用 STATUS_FAILED 常量
                    await crud_assessment.update_status(db=session, assessment_id=assessment_id, new_status=STATUS_FAILED)
                    logger.info(f"{task_id_str} 已尝试将 ID {assessment_id} 状态更新为失败 (导入错误)。")
            asyncio.run(update_fail_status())
        except Exception as db_err:
             logger.error(f"{task_id_str} 在更新失败状态时出错 (导入错误)，ID {assessment_id}: {db_err}")
        publish_report_status_sync(assessment_id, "failed", error_msg) # 这里仍然用字符串 "failed" 发布
        return {"status": "failure", "assessment_id": assessment_id, "error": error_msg}

    async def _run_analysis_async():
        nonlocal assessment_id
        report_text_to_save = "处理失败：发生未知错误"
        # 使用状态常量初始化
        final_status = STATUS_FAILED
        error_detail = None
        updated_to_complete = False

        async with AsyncSessionLocal() as session:
            try:
                logger.info(f"{task_id_str} 正在异步加载评估数据 ID: {assessment_id}")
                assessment_record = await crud_assessment.get(db=session, id=assessment_id)

                if not assessment_record:
                    logger.error(f"{task_id_str} 无法找到评估记录 ID: {assessment_id}")
                    error_detail = f"评估记录 ID {assessment_id} 未找到"
                    # 使用状态常量返回
                    return {"status": STATUS_FAILED, "assessment_id": assessment_id, "error": error_detail}

                # +++ 更新状态为 processing (使用常量) +++
                if assessment_record.status == STATUS_PENDING:
                    # 使用常量进行比较和更新
                    logger.info(f"{task_id_str} 将评估 ID {assessment_id} 状态更新为 '{STATUS_PROCESSING}'")
                    try:
                        await crud_assessment.update_status(db=session, assessment_id=assessment_id, new_status=STATUS_PROCESSING)
                    except Exception as status_update_err:
                         logger.error(f"{task_id_str} 更新状态为 processing 时出错 (ID: {assessment_id}): {status_update_err}", exc_info=True)
                # +++++++++++++++++++++++++++++++++++++++

                submission_data = {}
                for column in assessment_record.__table__.columns:
                    submission_data[column.name] = getattr(assessment_record, column.name)

                logger.debug(f"{task_id_str} 已加载数据，准备调用核心处理函数，ID: {assessment_id}")
                generated_text = generate_report_content(
                    submission_data=submission_data,
                    config=settings.model_dump(),
                    task_logger=logger
                )

                if generated_text is None:
                    logger.error(f"{task_id_str} 核心处理函数返回 None，ID: {assessment_id}")
                    report_text_to_save = "错误：报告生成意外返回空"
                    error_detail = "报告生成返回空"
                    final_status = STATUS_FAILED
                elif "错误" in generated_text or "Error" in generated_text or "失败" in generated_text:
                    logger.error(f"{task_id_str} 核心处理函数返回错误信息，ID {assessment_id}: {generated_text[:200]}...")
                    report_text_to_save = generated_text
                    error_detail = f"AI 处理失败: {generated_text[:150]}"
                    final_status = STATUS_FAILED
                else:
                    logger.info(f"{task_id_str} 报告内容生成成功，ID: {assessment_id}")
                    report_text_to_save = generated_text
                    # 使用状态常量
                    final_status = STATUS_COMPLETE
                    error_detail = None

                logger.info(f"{task_id_str} 尝试异步更新报告文本到数据库，ID: {assessment_id}")
                report_to_save_str = str(report_text_to_save)
                updated_record = await crud_assessment.update_report_text(
                    db=session,
                    assessment_id=assessment_id,
                    report_text=report_to_save_str
                )

                if not updated_record:
                    logger.error(f"{task_id_str} 尝试更新数据库时记录 ID {assessment_id} 未找到！")
                    if final_status == STATUS_COMPLETE: final_status = STATUS_FAILED # 使用常量
                    error_detail = f"数据库更新失败 (更新时 ID: {assessment_id} 未找到)"
                else:
                    logger.info(f"{task_id_str} 数据库报告文本更新成功，ID: {assessment_id}")
                    # +++++++ 如果报告文本更新成功，并且预期状态是 complete，则更新状态 (使用常量) +++++++
                    if final_status == STATUS_COMPLETE:
                        logger.info(f"{task_id_str} 尝试异步更新评估状态为 '{STATUS_COMPLETE}'，ID: {assessment_id}")
                        try:
                            status_updated_record = await crud_assessment.update_status(
                                db=session,
                                assessment_id=assessment_id,
                                new_status=STATUS_COMPLETE # 使用常量
                            )
                            if status_updated_record:
                                logger.info(f"{task_id_str} 数据库状态更新为 '{STATUS_COMPLETE}' 成功，ID: {assessment_id}")
                                updated_to_complete = True
                            else:
                                logger.error(f"{task_id_str} 更新状态为 '{STATUS_COMPLETE}' 时记录 ID {assessment_id} 未找到！")
                                final_status = STATUS_FAILED # 使用常量
                                error_detail = f"数据库状态更新失败 (更新时 ID: {assessment_id} 未找到)"
                        except Exception as status_update_err:
                            logger.error(f"{task_id_str} 更新状态为 '{STATUS_COMPLETE}' 时出错，ID {assessment_id}: {status_update_err}", exc_info=True)
                            error_detail = f"数据库状态更新时出错: {status_update_err}"
                    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

            except Exception as e:
                logger.error(f"{task_id_str} 在 _run_analysis_async 中发生意外错误，ID {assessment_id}: {e}", exc_info=True)
                error_message = f"任务执行失败: {type(e).__name__} - {str(e)}"
                report_text_to_save = error_message[:2000]
                final_status = STATUS_FAILED # 使用常量
                error_detail = error_message[:150]
                try:
                    logger.info(f"{task_id_str} 尝试将错误信息和失败状态写入数据库，ID {assessment_id}")
                    await crud_assessment.update_report_text(
                         db=session,
                         assessment_id=assessment_id,
                         report_text=report_text_to_save
                     )
                    # 使用常量更新状态
                    await crud_assessment.update_status(
                         db=session,
                         assessment_id=assessment_id,
                         new_status=STATUS_FAILED
                     )
                    logger.info(f"{task_id_str} 已将最终错误信息和失败状态写入数据库，ID {assessment_id}")
                except Exception as db_err_on_fail:
                    logger.error(f"{task_id_str} 在失败处理中写入数据库也失败了，ID {assessment_id}: {db_err_on_fail}")

        # 返回最终状态 (常量)，以及其他信息
        return {"status": final_status, "report_text": report_text_to_save, "error": error_detail, "updated_to_complete": updated_to_complete}

    # --- 运行异步块并发布状态 (使用常量) ---
    result = None
    final_task_status = STATUS_FAILED # 使用常量
    report_length = 0
    error_for_publish = "任务执行期间发生未知错误"
    publish_status_str = "failed" # 用于发布到 Redis 的状态字符串，保持 success/failed

    try:
        result = asyncio.run(_run_analysis_async())
        final_task_status = result.get("status", STATUS_FAILED)
        error_for_publish = result.get("error")

        if final_task_status == STATUS_COMPLETE and result.get("updated_to_complete"):
            report_length = len(result.get("report_text", ""))
            error_for_publish = None
            publish_status_str = "success" # Redis 发布 success
        elif final_task_status == STATUS_COMPLETE and not result.get("updated_to_complete"):
             logger.warning(f"{task_id_str} 任务成功完成但状态更新至DB失败，ID {assessment_id}。错误: {error_for_publish}")
             error_for_publish = "报告已生成，但最终状态更新至数据库时出错。"
             publish_status_str = "success" # 核心完成，仍发布 success
        else: # 任务失败
             logger.error(f"{task_id_str} 任务处理失败，ID {assessment_id}。错误: {error_for_publish}")
             publish_status_str = "failed" # Redis 发布 failed

        # *** 同步发布最终状态到 Redis (使用 "success" 或 "failed" 字符串) ***
        publish_report_status_sync(assessment_id, publish_status_str, error_for_publish)

    except Exception as task_exec_err:
        logger.critical(f"{task_id_str} Celery 任务执行期间发生顶层错误，ID {assessment_id}: {task_exec_err}", exc_info=True)
        error_msg = f"任务执行错误: {type(task_exec_err).__name__} - {str(task_exec_err)}"
        error_for_publish = error_msg[:150]
        final_task_status = STATUS_FAILED # 使用常量
        publish_status_str = "failed"     # Redis 发布 failed

        try:
            from src.data_handler import DataHandler
            sync_db_path = settings.DB_PATH_SQLITE
            sync_handler = DataHandler(db_path=sync_db_path)
            sync_handler.update_report_text(assessment_id, error_msg[:2000])
            # sync_handler.update_status(assessment_id, STATUS_FAILED) # 假设有同步更新状态方法
            logger.info(f"{task_id_str} 已尝试同步记录顶层错误到数据库，ID {assessment_id}")
        except Exception as sync_db_err:
            logger.error(f"{task_id_str} 同步记录顶层错误到数据库失败，ID {assessment_id}: {sync_db_err}")
        finally:
             publish_report_status_sync(assessment_id, publish_status_str, error_for_publish)

    # --- 返回任务结果 (使用 "success" 或 "failure" 字符串，与 Redis 发布一致) ---
    logger.info(f"{task_id_str} 任务处理完成，ID {assessment_id}, 结果: {final_task_status}")
    if final_task_status == STATUS_COMPLETE:
        return {"status": "success", "assessment_id": assessment_id, "report_length": report_length, "db_status_updated": result.get("updated_to_complete", False)}
    else:
        return {"status": "failure", "assessment_id": assessment_id, "error": error_for_publish}