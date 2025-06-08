# FILE: app/routers/assessments.py (修改后)
import logging
import os
import json
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form, Request, status
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
# --- 修改: 导入更具体的数据库异常 ---
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

# --- 核心应用导入 ---
from app.core.config import settings
from app.schemas.assessment import AssessmentSubmitResponse
# 确保 Celery 任务可导入
try:
    from app.tasks.analysis import run_ai_analysis
except ImportError:
    run_ai_analysis = None # 如果导入失败，定义为 None
    logging.getLogger(settings.APP_NAME or "FallbackLogger").error("未能导入 Celery 任务 'run_ai_analysis'。后台处理已禁用。")

# --- 认证与数据库导入 ---
from app.core.deps import get_current_active_user, get_db # 使用异步 get_db
from app import models, schemas # 导入 schemas 供潜在使用
# 导入主 crud 包 (确保 app/crud/__init__.py 导入了 assessment)
from app import crud

# --- 工具函数 ---
try:
    from werkzeug.utils import secure_filename
except ImportError:
    import re
    def secure_filename(filename: str) -> str:
        """
        一个 werkzeug.utils.secure_filename 的基本替代实现。
        限制字符集并防止路径遍历。
        """
        if not filename:
            return "invalid_filename"
        # 移除不安全的字符
        filename = re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)
        # 移除开头/结尾的点或下划线
        filename = filename.strip('._')
        # 防止文件名变为空
        return filename if filename else "invalid_filename"
    # 安全地获取 logger
    logging.getLogger(settings.APP_NAME or "FallbackLogger").warning("未安装 werkzeug。使用基本的 secure_filename 备用方案。")

# 使用配置的应用 logger
logger = logging.getLogger(settings.APP_NAME)
router = APIRouter()

# --- API 端点 ---
@router.post(
    "/assessments/submit",
    response_model=AssessmentSubmitResponse,
    tags=["Assessments"],
    status_code=status.HTTP_202_ACCEPTED # 成功时返回 202 Accepted
)
async def submit_assessment(
    # --- 依赖 ---
    db: AsyncSession = Depends(get_db),
    request: Request = None, # 保留用于解析表单数据
    current_user: models.User = Depends(get_current_active_user), # 认证依赖

    # --- 表单字段 (名称需与 JS 中的 FormData 匹配) ---
    name: str = Form(..., description="姓名"),
    gender: str = Form(..., description="性别"),
    age: int = Form(..., gt=0, description="年龄"),
    id_card: Optional[str] = Form(None, description="身份证号"),
    occupation: Optional[str] = Form(None, description="职业"),
    case_name: Optional[str] = Form(None, description="案件名称"),
    case_type: Optional[str] = Form(None, description="案件类型"),
    identity_type: Optional[str] = Form(None, description="人员身份"),
    person_type: Optional[str] = Form(None, description="人员类型"),
    marital_status: Optional[str] = Form(None, description="婚姻状况"),
    children_info: Optional[str] = Form(None, description="子女情况"),
    criminal_record: Optional[int] = Form(0, ge=0, le=1, description="有无犯罪前科 (0:无, 1:有)"),
    health_status: Optional[str] = Form(None, description="健康情况"),
    phone_number: Optional[str] = Form(None, description="手机号"),
    domicile: Optional[str] = Form(None, description="归属地"),
    scale_type: Optional[str] = Form(None, description="选择的量表代码"),
    # 确保 'image' 匹配 HTML/JS 中文件输入的 name 属性
    image: Optional[UploadFile] = File(None, description="上传的绘画图片")
):
    """
    接收来自已认证用户的评估数据。
    保存数据并排队等待后台 AI 分析任务。
    """
    # +++ 在潜在的数据库错误发生前获取用户名和 ID +++
    submitter_username = current_user.username
    submitter_id = current_user.id
    logger.info(f"用户 '{submitter_username}' (ID: {submitter_id}) 正在提交新的评估，主体姓名: {name}")

    # --- 1. 收集基础信息 (将表单字段映射到数据库模型字段) ---
    basic_info: Dict[str, Any] = {
        "subject_name": name, # 将表单的 'name' 映射到数据库模型的 'subject_name'
        "gender": gender,
        "age": age,
        "id_card": id_card,
        "occupation": occupation,
        "case_name": case_name,
        "case_type": case_type,
        "identity_type": identity_type,
        "person_type": person_type,
        "marital_status": marital_status,
        "children_info": children_info,
        "criminal_record": criminal_record, # 已经是 int 0 或 1
        "health_status": health_status,
        "phone_number": phone_number,
        "domicile": domicile,
        "submitter_id": submitter_id # 添加认证用户的 ID
    }
    logger.debug(f"收集的基础信息 (待存入数据库): {basic_info}")

    # --- 2. 处理图片上传 ---
    image_relative_path: Optional[str] = None
    image_full_path: Optional[str] = None # 跟踪完整路径以备保存
    image_was_saved_to_disk: bool = False # 标记，以便在出错时清理

    if image and image.filename:
        # 清理文件名
        original_filename = secure_filename(image.filename)
        if original_filename == "invalid_filename":
             logger.warning(f"用户 {submitter_username} 上传了无效的文件名 '{image.filename}'。")
             # 可选择抛出 HTTPException 或在没有图片的情况下继续
             # raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无效的文件名。")
             image = None # 视为未上传图片

        if image: # 再次检查文件名检查后 image 是否仍然有效
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            # 使用身份证号（如果提供）或姓名（如果提供）或 'UnknownID' 作为文件名的一部分
            id_part = secure_filename(id_card if id_card else (name if name else 'UnknownID'))
            base, ext = os.path.splitext(original_filename)
            safe_base = base[:50] # 限制基本文件名长度
            # 标准化扩展名为小写
            ext_lower = ext.lower()
            # 允许的文件类型示例
            allowed_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}
            if ext_lower not in allowed_extensions:
                logger.warning(f"用户 {submitter_username} 上传了不允许的文件类型: {ext_lower}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"不允许的文件类型: {ext}. 请上传 {', '.join(allowed_extensions)} 格式的文件。"
                )

            # 构建用于保存的安全文件名
            image_filename_to_save = f"{id_part}_{timestamp}_{safe_base}{ext_lower}"
            image_full_path = os.path.join(settings.UPLOADS_DIR, image_filename_to_save)
            # 在数据库中存储相对路径（或仅文件名）
            image_relative_path = image_filename_to_save # 或根据你提供文件的方式进行调整

            try:
                # 确保上传目录存在
                os.makedirs(settings.UPLOADS_DIR, exist_ok=True)
                # 异步读取文件内容并保存
                file_content = await image.read()
                with open(image_full_path, "wb") as buffer:
                    buffer.write(file_content)
                image_was_saved_to_disk = True # 标记为已保存，以备潜在清理
                logger.info(f"图片由用户 {submitter_username} 保存至: {image_full_path}")
            except OSError as e: # 捕获文件系统相关的错误
                logger.error(f"用户 {submitter_username} 保存上传图片至 {image_full_path} 时发生文件系统错误: {e}", exc_info=True)
                # 如果保存失败则不继续，通知用户
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"保存上传文件时发生服务器错误。")
            except Exception as e:
                logger.error(f"用户 {submitter_username} 保存上传图片至 {image_full_path} 时发生未知错误: {e}", exc_info=True)
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"处理上传文件时发生意外错误。")
            finally:
                 # 确保文件被关闭 (UploadFile 应该会处理这个，但这是好习惯)
                 await image.close()
    else:
        logger.info(f"用户 {submitter_username} 未上传图片。")

    # --- 3. 收集量表答案 (从动态表单字段 q1, q2...) ---
    scale_answers_dict: Dict[str, Any] = {}
    scale_answers_json: Optional[str] = None
    if scale_type:
        if request is None:
             logger.error("未注入 Request 对象，无法解析量表答案。这是一个服务器配置问题。")
             # 这表示服务器端设置问题
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="内部服务器错误: 无法访问请求对象。")
        try:
            # 异步获取所有表单数据
            form_data = await request.form()
            for key, value in form_data.items():
                # 检查 key 是否以 'q' 开头后跟数字
                if key.startswith('q') and key[1:].isdigit():
                    # 尝试将值转换为数字（如果可能），否则保持字符串
                    try:
                        scale_answers_dict[key] = int(value)
                    except ValueError:
                        try:
                            scale_answers_dict[key] = float(value)
                        except ValueError:
                            scale_answers_dict[key] = value # 保留为字符串

            if scale_answers_dict:
                # 将收集到的答案转换为 JSON 字符串以便数据库存储
                scale_answers_json = json.dumps(scale_answers_dict, ensure_ascii=False, sort_keys=True) # 排序以保证一致性
                logger.info(f"用户 {submitter_username} 为量表 '{scale_type}' 收集到的答案: {len(scale_answers_dict)} 条")
                logger.debug(f"量表答案 (JSON): {scale_answers_json}")
            else:
                logger.warning(f"用户 {submitter_username} 提供了量表类型 '{scale_type}', 但未在表单中找到以 'q' 开头的答案。")
                # 根据需求，你可能需要抛出错误或允许提交时没有答案
                # raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"选择了量表 '{scale_type}' 但未提供答案。")
        except Exception as e:
             logger.error(f"用户 {submitter_username} 解析量表答案时出错: {e}", exc_info=True)
             # 在没有量表数据的情况下继续或抛出错误
             scale_answers_json = None # 确保如果解析失败则为 None
             # raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"解析量表答案时出错: {e}")

    # --- 4. 使用异步 CRUD 保存初始数据 ---
    assessment_id: Optional[int] = None
    new_assessment: Optional[models.Assessment] = None # 初始化为 None
    try:
        # --- *** 通过导入的 crud 包访问 assessment CRUD *** ---
        # 现在需要 app/crud/__init__.py 包含 `from . import assessment`
        new_assessment = await crud.assessment.create(
            db=db,
            # 使用与 Assessment 模型字段匹配的关键字参数传递收集的数据
            **basic_info, # 解包基础信息字典
            image_path=image_relative_path, # 存储相对路径/文件名
            questionnaire_type=scale_type,
            questionnaire_data=scale_answers_json, # 存储 JSON 字符串
            report_text=None # 初始报告文本为空
        )
        # --- 移除这里的检查，因为 CRUD 函数现在保证返回有效对象或抛出异常 ---
        # if not new_assessment or not hasattr(new_assessment, 'id'):
        #     raise ValueError("数据保存操作未返回有效的评估对象ID。")

        # 现在可以安全获取 ID (假设 create 成功时总会提交并刷新对象)
        # 注意: 如果 create 内部没有 commit/refresh, ID 可能还是 None
        # 确保 crud.assessment.create 在成功时返回带有 ID 的对象
        if new_assessment and new_assessment.id:
            assessment_id = new_assessment.id
            logger.info(f"评估数据由用户 {submitter_username} 保存成功。评估 ID: {assessment_id}")
        else:
             # 这是一个异常情况，如果 CRUD 成功但没有 ID
             logger.error(f"用户 {submitter_username} 的评估数据似乎已保存，但未能获取 ID。CRUD 实现可能需要检查。")
             raise SQLAlchemyError("数据库操作成功，但未能检索到新记录的 ID。") # 抛出一个通用的 DB 错误

    except IntegrityError as ie: # --- 捕获 IntegrityError (例如，唯一约束冲突) ---
        logger.warning(f"用户 {submitter_username} 保存评估数据时发生数据库完整性错误: {ie}", exc_info=True)
        await db.rollback() # 回滚数据库事务
        # 清理可能已保存的图片
        if image_was_saved_to_disk and image_full_path and os.path.exists(image_full_path):
            try:
                os.remove(image_full_path)
                logger.info(f"因数据库完整性错误清理了文件 {image_full_path}")
            except Exception as rm_err:
                logger.warning(f"数据库完整性错误后无法移除文件 {image_full_path}: {rm_err}")
        # 返回 409 Conflict 状态码
        # 可以根据具体错误 (ie.args) 提供更具体的 detail，但要小心暴露内部信息
        error_detail = "数据保存冲突。可能某个唯一字段（如身份证号）已存在。"
        # 检查是否是特定的唯一约束错误，例如，如果你的身份证字段有唯一约束 'uq_assessment_id_card'
        # if "uq_assessment_id_card" in str(ie).lower():
        #     error_detail = "保存失败：该身份证号已被使用。"
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error_detail)

    except TypeError as te: # --- 捕获 TypeError (通常来自模型初始化时字段类型不匹配) ---
        logger.warning(f"用户 {submitter_username} 提交的数据字段与预期模型类型不匹配: {te}", exc_info=True)
        await db.rollback() # 尽管可能还没到数据库操作，回滚以防万一
        # 清理可能已保存的图片
        if image_was_saved_to_disk and image_full_path and os.path.exists(image_full_path):
             try:
                 os.remove(image_full_path)
                 logger.info(f"因类型错误清理了文件 {image_full_path}")
             except Exception as rm_err:
                 logger.warning(f"类型错误后无法移除文件 {image_full_path}: {rm_err}")
        # 返回 422 Unprocessable Entity 状态码，表示数据无法处理
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"提交的数据字段无效或类型错误: {te}")

    except SQLAlchemyError as dbe: # --- 捕获其他 SQLAlchemy 相关错误 (连接、其他约束等) ---
         logger.error(f"用户 {submitter_username} 保存评估数据时发生数据库操作错误: {dbe}", exc_info=True)
         await db.rollback() # 回滚数据库事务
         # 清理可能已保存的图片
         if image_was_saved_to_disk and image_full_path and os.path.exists(image_full_path):
             try:
                 os.remove(image_full_path)
                 logger.info(f"因数据库操作错误清理了文件 {image_full_path}")
             except Exception as rm_err:
                 logger.warning(f"数据库操作错误后无法移除文件 {image_full_path}: {rm_err}")
         # 返回 500 Internal Server Error
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"数据库操作失败。请稍后重试或联系管理员。")

    except Exception as e: # --- 捕获所有其他意外错误 ---
        logger.error(f"用户 {submitter_username} 处理评估提交时发生意外错误: {e}", exc_info=True)
        await db.rollback() # 尝试回滚以防万一
        # 清理可能已保存的图片
        if image_was_saved_to_disk and image_full_path and os.path.exists(image_full_path):
            try:
                os.remove(image_full_path)
                logger.info(f"因意外错误清理了文件 {image_full_path}")
            except Exception as rm_err:
                logger.warning(f"意外错误后无法移除文件 {image_full_path}: {rm_err}")
        # 返回 500 Internal Server Error
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"处理请求时发生内部服务器错误。")

    # --- 5. 触发 Celery 任务 (仅当 assessment_id 成功获取后执行) ---
    task_id: Optional[str] = None
    if assessment_id: # 只有在数据成功保存并获取 ID 后才排队
        if run_ai_analysis:
            try:
                # 仅传递任务所需的 ID
                task = run_ai_analysis.delay(assessment_id)
                task_id = task.id
                logger.info(f"已为评估 ID: {assessment_id} (提交者: {submitter_username}) 排队 AI 分析任务。任务 ID: {task_id}")
            except Exception as celery_err:
                 # 记录错误，但请求本身是成功的（数据已保存）
                 logger.error(f"为评估 ID {assessment_id} (提交者: {submitter_username}) 排队 Celery 任务失败: {celery_err}", exc_info=True)
                 # 不要在此处引发 HTTPException，因为主要操作（保存数据）已成功。
                 # 响应消息将指示排队失败。
        else:
             logger.warning(f"Celery 任务 'run_ai_analysis' 未加载或不可用。评估 ID: {assessment_id} 的后台处理将不会运行。")

    # --- 6. 构建 API 响应 (基于成功保存和任务排队状态) ---
    if assessment_id:
        status_code_resp: str
        message: str
        if task_id:
            message = "评估数据已接收，正在后台进行 AI 分析。"
            status_code_resp = "processing_queued" # 状态码：处理已排队
        elif run_ai_analysis is None: # 检查任务函数本身是否为 None
            message = f"评估数据已接收 (ID: {assessment_id})，但后台分析任务未配置或导入失败。"
            status_code_resp = "warning_task_unavailable" # 状态码：警告，任务不可用
        else: # 任务函数存在但 .delay() 失败
            message = f"评估数据已接收 (ID: {assessment_id})，但启动后台处理任务时出错。"
            status_code_resp = "warning_queueing_failed" # 状态码：警告，排队失败

        return AssessmentSubmitResponse(
            status=status_code_resp,
            message=message,
            submission_id=assessment_id
            # task_id=task_id # 可选地在响应中包含 task_id
        )
    else:
        # 理论上，如果上面的异常处理正确，这个情况不应该发生
        logger.error(f"评估 ID 未能生成，但未捕获到明确异常。提交者: {submitter_username}。这可能表示 CRUD 函数实现有问题。")
        # 即使没有 assessment_id，如果代码执行到这里，意味着没有抛出预期的异常
        # 但这仍然是一个错误状态，因为我们期望有 ID
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="数据似乎已保存，但在获取确认 ID 时遇到问题。")