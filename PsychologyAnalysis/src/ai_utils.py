# src/ai_utils.py
import os
import json
# 移除了 import sqlite3
from datetime import datetime
import sys
import logging

# --- 路径设置和模块导入 (保持不变) ---
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT_FROM_SRC = os.path.dirname(SRC_DIR)
if PROJECT_ROOT_FROM_SRC not in sys.path:
    sys.path.insert(0, PROJECT_ROOT_FROM_SRC)

try:
    # 移除了 from .data_handler import DataHandler 的导入，因为此文件不再直接使用它
    # 修正：确认导入路径
    from src.image_processor import ImageProcessor
    from src.report_generator import ReportGenerator
    print("[ai_utils] 成功相对导入 ImageProcessor 和 ReportGenerator。")
except ImportError:
    try:
        # 移除了 from data_handler import DataHandler 的导入
        from image_processor import ImageProcessor
        from report_generator import ReportGenerator
        print("[ai_utils] 成功直接导入 ImageProcessor 和 ReportGenerator (后备)。")
    except ImportError as e:
        print(f"[ai_utils] CRITICAL ERROR: 无法导入必要的同级模块: {e}", file=sys.stderr)
        # 如果在 Celery 任务中，这可能导致任务失败
        raise e

# --- calculate_score_and_interpret 函数 (添加 HappyTest 逻辑) ---
def calculate_score_and_interpret(scale_type, scale_answers, task_logger=None):
    """
    根据量表答案计算分数，并根据量表类型提供基本解释。
    使用提供的 logger 实例进行日志记录。

    Args:
        scale_type (str): 表示量表类型的代码 (例如, 'SAS', 'SDS').
        scale_answers (dict): 问题答案字典 { 'q1': 'score_value', ... }.
        task_logger (logging.Logger, optional): 要使用的 Logger 实例. 默认为 None.

    Returns:
        tuple: (calculated_score, interpretation_string)
    """
    # 获取 logger，如果未提供则使用默认 logger
    current_logger = task_logger or logging.getLogger(__name__)
    if task_logger is None:
        current_logger.warning("未向 calculate_score_and_interpret 提供 task_logger，使用默认日志记录器。")
        # 确保有基本的日志处理器，以防万一
        if not logging.getLogger().hasHandlers():
            logging.basicConfig(level=logging.INFO)

    # 处理没有答案的情况
    if not scale_answers:
        current_logger.info(f"量表类型 '{scale_type}' 的答案为空。")
        return 0, "无量表答案"

    calculated_score = 0
    try:
        # 确保值存在且可以转换为数字
        valid_scores = []
        for key, value in scale_answers.items():
            if value is not None:
                try:
                    # 尝试转换为浮点数，然后转整数（如果可能）
                    score_float = float(value)
                    # 检查是否为整数
                    if score_float.is_integer():
                         valid_scores.append(int(score_float))
                    else:
                         valid_scores.append(score_float)
                except (ValueError, TypeError):
                    current_logger.warning(f"无法将答案 '{key}':'{value}' 转换为数字，已忽略。")

        # 如果没有任何有效分数
        if not valid_scores:
             current_logger.warning(f"在类型 {scale_type} 的量表答案中未找到有效的数字分数: {scale_answers}")
             return 0, f"量表 '{scale_type}' 无有效得分项"

        # 计算总分
        calculated_score = sum(valid_scores)
        current_logger.debug(f"计算得到的分数: {calculated_score} (来自: {valid_scores})")
    except Exception as e:
        current_logger.error(f"从答案 {scale_answers} 计算分数时出错: {e}", exc_info=True)
        # 返回错误标记和信息
        return "计算错误", f"分数计算出错: {e}"

    # --- 量表解释逻辑 ---
    interpretation = f"量表 '{scale_type}' 总得分: {calculated_score}."
    current_logger.info(f"开始为量表 '{scale_type}' (得分: {calculated_score}) 生成解释。")

    try:
        # --- 添加或更新解释逻辑 ---
        if scale_type == 'SAS': # Anxiety Self-Rating Scale
            standard_score = int(calculated_score * 1.25)
            interpretation = f"量表 '{scale_type}' 原始得分: {calculated_score}, 标准分: {standard_score}."
            if standard_score >= 70: interpretation += " (重度焦虑水平)"
            elif standard_score >= 60: interpretation += " (中度焦虑水平)"
            elif standard_score >= 50: interpretation += " (轻度焦虑水平)"
            else: interpretation += " (焦虑水平在正常范围)"
        elif scale_type == 'SDS': # Depression Self-Rating Scale
             standard_score = int(calculated_score * 1.25)
             interpretation = f"量表 '{scale_type}' 原始得分: {calculated_score}, 标准分: {standard_score}."
             if standard_score >= 73: interpretation += " (重度抑郁水平)" # 按量表文件界限
             elif standard_score >= 63: interpretation += " (中度抑郁水平)"
             elif standard_score >= 53: interpretation += " (轻度抑郁水平)"
             else: interpretation += " (抑郁水平在正常范围)"
        elif scale_type == 'ParentChild':
            if calculated_score >= 80: interpretation += " (亲子关系非常和谐)"
            elif calculated_score >= 60: interpretation += " (亲子关系良好)"
            else: interpretation += " (亲子关系可能存在挑战，建议关注)"
        elif scale_type == 'Personality':
            if calculated_score >= 101: interpretation += " (倾向：积极热情)"
            elif calculated_score >= 90: interpretation += " (倾向：领导人特质)"
            elif calculated_score >= 79: interpretation += " (倾向：感性)"
            elif calculated_score >= 60: interpretation += " (倾向：理性&淡定)"
            elif calculated_score >= 40: interpretation += " (倾向：双重&孤寂)"
            else: interpretation += " (倾向：现实&自我)"
            interpretation += " (具体解释需参考原始量表得分范围)"
        elif scale_type == 'InterpersonalRelationship':
            if calculated_score <= 8: interpretation += " (人际关系困扰较少)"
            elif calculated_score <= 14: interpretation += " (人际关系存在一定困扰)"
            else: interpretation += " (人际关系困扰较严重)"
        elif scale_type == 'EmotionalStability':
             if calculated_score <= 20: interpretation += " (情绪稳定，自信心强)"
             elif calculated_score <= 40: interpretation += " (情绪基本稳定，但可能较为深沉或消极)"
             else: interpretation += " (情绪不稳定，可能需要关注)"
        elif scale_type == 'HAMD24':
            if calculated_score >= 36: interpretation += " (重度抑郁)"
            elif calculated_score >= 21: interpretation += " (肯定有抑郁)"
            elif calculated_score >= 8: interpretation += " (可能有抑郁)"
            else: interpretation += " (无抑郁症状)"
        elif scale_type == 'EPQ85':
             interpretation = f"艾森克人格问卷 (EPQ-85)，总得分无直接意义，需分析 P, E, N, L 各维度得分。"
             # 实际分析需要在 generate_report_content 中单独处理 EPQ85
        # +++ 添加 HappyTest 的解释 +++
        elif scale_type == 'HappyTest':
             if calculated_score == 1:
                  interpretation += " (初步判断：用户表示今天很开心。)"
             elif calculated_score == 0:
                  interpretation += " (初步判断：用户表示今天感到悲伤。)"
             else:
                  interpretation += " (得分异常，无法解释。)" # 处理意外得分
        # --- HappyTest 解释结束 ---
        else:
            # 未知量表类型
            current_logger.warning(f"未找到量表类型 '{scale_type}' 的特定解释规则。")
            interpretation += " (无特定解释规则)"

    except Exception as e:
        current_logger.error(f"量表 {scale_type} 解释过程中出错: {e}", exc_info=True)
        interpretation += " (解释规则应用出错)"

    current_logger.info(f"量表 '{scale_type}' 解释完成: '{interpretation}'")
    return calculated_score, interpretation


# --- 重命名并重构核心函数 ---
def generate_report_content(submission_data: dict, config: dict, task_logger: logging.Logger) -> str:
    """
    根据传入的评估数据和配置，生成报告文本。不再直接操作数据库。

    Args:
        submission_data (dict): 从数据库异步加载的评估数据字典.
        config (dict): 应用程序配置字典 (来自 settings.model_dump()).
        task_logger (logging.Logger): 用于记录日志的 logger 实例.

    Returns:
        str: 生成的报告文本或错误信息字符串.
    """
    logger = task_logger
    submission_id = submission_data.get("id", "未知ID")
    logger.info(f"开始为评估 ID: {submission_id} 生成报告内容")

    # --- 提取数据 ---
    image_filename = submission_data.get('image_path') # 这是存储在 DB 中的相对路径或文件名
    image_full_path = None
    if image_filename:
        # 从配置中获取上传目录
        uploads_dir = config.get("UPLOADS_DIR")
        if uploads_dir and os.path.isdir(uploads_dir):
            image_full_path = os.path.join(uploads_dir, image_filename)
            logger.info(f"将使用的图片文件路径: {image_full_path}")
        elif not uploads_dir:
            logger.warning(f"配置中未找到 UPLOADS_DIR，无法定位图片文件: {image_filename}")
        else: # uploads_dir 存在但不是目录
             logger.warning(f"配置的 UPLOADS_DIR '{uploads_dir}' 不是有效目录，无法定位图片文件: {image_filename}")

    scale_type = submission_data.get('questionnaire_type')
    scale_answers_json = submission_data.get('questionnaire_data')
    # 确保 basic_info 包含所有可能的键，并提供默认值
    basic_info = {
        "subject_name": submission_data.get("subject_name", '未提供'),
        "gender": submission_data.get("gender", '未提供'),
        "id_card": submission_data.get("id_card", '未提供'),
        "age": submission_data.get("age", '未提供'),
        "occupation": submission_data.get("occupation", '未提供'),
        "case_name": submission_data.get("case_name", '未提供'),
        "case_type": submission_data.get("case_type", '未提供'),
        "identity_type": submission_data.get("identity_type", '未提供'),
        "person_type": submission_data.get("person_type", '未提供'),
        "marital_status": submission_data.get("marital_status", '未提供'),
        "children_info": submission_data.get("children_info", '未提供'),
        "criminal_record": submission_data.get("criminal_record", 0), # 默认 0 (无)
        "health_status": submission_data.get("health_status", '未提供'),
        "phone_number": submission_data.get("phone_number", '未提供'),
        "domicile": submission_data.get("domicile", '未提供')
    }
    # 确保 'name' 键存在，用于报告模板
    basic_info['name'] = basic_info.get('subject_name', '未知')

    logger.debug(f"用于报告生成的基础信息 (ID {submission_id}): {basic_info}")

    # --- 准备 AI 配置 ---
    ai_config = config.copy()
    # 确保 api_key 存在
    if 'api_key' not in ai_config:
        api_key_from_env = config.get('DASHSCOPE_API_KEY')
        if api_key_from_env:
            logger.info("复制 DASHSCOPE_API_KEY 到 'api_key' 以供 AI 处理器使用。")
            ai_config['api_key'] = api_key_from_env
        else:
             logger.error(f"CRITICAL: AI 处理器的 API Key 未在配置中找到! (ID: {submission_id})")
             # 返回错误信息，因为无法继续
             return "错误：AI 服务配置不完整 (缺少 API Key)"

    # --- 处理图片 ---
    image_description = "未提供图片"
    if image_full_path:
        if os.path.exists(image_full_path):
            logger.info(f"开始处理图片: {image_full_path}")
            try:
                # 使用配置初始化 ImageProcessor
                image_processor = ImageProcessor(ai_config)
                image_description = image_processor.process_image(image_full_path)
                logger.info(f"图片描述生成成功 (ID {submission_id})。描述片段: {image_description[:100]}...")
            except FileNotFoundError:
                 logger.error(f"图片文件在处理时未找到: {image_full_path}")
                 image_description = "图片文件未找到"
            except Exception as img_err:
                logger.error(f"图片处理失败 (ID {submission_id}): {img_err}", exc_info=True)
                image_description = f"图片处理错误: {img_err}"
        else:
            logger.warning(f"图片路径存在但文件在处理时未找到: {image_full_path}")
            image_description = "图片文件未找到"
    else:
        logger.info(f"评估 ID {submission_id} 未提供图片路径。")

    # --- 处理量表数据 ---
    scale_answers = None
    calculated_score = 0 # Default score
    scale_interpretation = "无量表数据" # Default interpretation

    if scale_type and scale_answers_json:
        logger.info(f"开始处理量表数据，类型: {scale_type} (ID {submission_id})")
        try:
            # 尝试解析 JSON 字符串
            scale_answers = json.loads(scale_answers_json) # 期望是字典 {'q1': 'score', ...}

            # 检查解析结果是否为字典
            if isinstance(scale_answers, dict):
                 # 特殊处理 EPQ85，因为它需要计算四个维度
                 if scale_type == 'EPQ85':
                      # TODO: 实现 EPQ85 的计分逻辑
                      # 这需要访问 EPQ85 的 JSON 文件来获取计分规则
                      # 假设有一个辅助函数 `calculate_epq85_scores(scale_answers)`
                      # 返回 {'P': score_p, 'E': score_e, 'N': score_n, 'L': score_l, 'interpretation': '...'}
                      # epq_results = calculate_epq85_scores(scale_answers, logger)
                      # calculated_score = epq_results # 或者只用某个主维度
                      # scale_interpretation = epq_results['interpretation']
                      logger.warning(f"EPQ85 量表计分逻辑尚未在此函数中完全实现 (ID: {submission_id})。")
                      calculated_score = "N/A" # 标记为不适用总分
                      scale_interpretation = "EPQ85 量表结果需单独分析各维度。"
                 else:
                     # 对于其他量表，使用通用计分函数
                     calculated_score, scale_interpretation = calculate_score_and_interpret(
                         scale_type, scale_answers, task_logger=logger
                     )
                 logger.info(f"量表处理完成: Score={calculated_score}, Interpretation='{scale_interpretation}' (ID {submission_id})")
            else:
                 # 如果 JSON 解析后不是字典
                 logger.error(f"解析后的量表答案不是字典类型 (ID {submission_id}): {type(scale_answers)}")
                 scale_interpretation = "量表答案格式错误 (非字典)"
                 scale_answers = None # 重置为 None，以免传递错误类型给报告生成器

        except json.JSONDecodeError as json_err:
            # JSON 字符串本身格式错误
            logger.error(f"量表答案 JSON 解析失败 (ID {submission_id}): {json_err}. JSON: {scale_answers_json[:200]}...")
            scale_interpretation = "量表答案格式错误 (JSON 解析失败)"
            scale_answers = None
        except Exception as scale_err:
            # 其他处理错误（如计分函数内部错误）
            logger.error(f"量表数据处理失败 (ID {submission_id}): {scale_err}", exc_info=True)
            scale_interpretation = f"量表处理错误: {scale_err}"
            scale_answers = None # 重置
    elif scale_type:
         # 有类型但无答案数据
         logger.warning(f"提供了量表类型 '{scale_type}' 但无答案数据 (ID {submission_id}).")
         scale_interpretation = f"量表 '{scale_type}' 未提供答案"
    else:
         # 没有提供量表类型
         logger.info(f"评估 ID {submission_id} 未提供量表类型.")

    # --- 调用 LLM 生成报告 ---
    logger.info(f"开始调用 LLM 生成报告 (ID {submission_id})")
    final_report_text = None
    try:
        # 使用配置初始化 ReportGenerator
        report_generator = ReportGenerator(ai_config)
        final_report_text = report_generator.generate_report(
             description=image_description,
             questionnaire=scale_answers, # 传递解析后的字典或 None
             subject_info=basic_info,
             questionnaire_type=scale_type if scale_type else "未指定", # 提供默认值
             score=calculated_score, # 可能是数字，也可能是 "N/A" (如 EPQ)
             scale_interpretation=scale_interpretation # 使用上面处理后的解释
         )
        # 检查 ReportGenerator 的返回值
        if final_report_text is None:
             # ReportGenerator 应该返回字符串，即使是错误信息
             logger.error(f"报告生成器意外返回了 None (ID: {submission_id})")
             raise ValueError("报告生成器意外返回了 None") # 抛出错误以便捕获
        logger.info(f"LLM 报告生成成功 (ID {submission_id}, 长度: {len(final_report_text)})")

    except Exception as report_err:
        logger.error(f"LLM 报告生成失败 (ID {submission_id}): {report_err}", exc_info=True)
        # 返回具体的错误信息，而不是仅仅标记失败
        final_report_text = f"报告生成错误: {type(report_err).__name__} - {str(report_err)}"

    # --- 返回最终文本 ---
    # 注意：此函数不再负责数据库更新
    return final_report_text

# 移除旧的 process_data_and_generate_report_sync 函数定义（如果它还存在）