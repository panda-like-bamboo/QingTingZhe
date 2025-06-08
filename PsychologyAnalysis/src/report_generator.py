# src/report_generator.py
from openai import OpenAI
import json
import os
import logging
import sys # 添加sys导入

# --- 导入 settings ---
# 确保路径正确，以便能够导入 settings
SRC_DIR_REPORT_GEN = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT_REPORT_GEN = os.path.dirname(SRC_DIR_REPORT_GEN) # PsychologyAnalysis/
if PROJECT_ROOT_REPORT_GEN not in sys.path:
    sys.path.insert(0, PROJECT_ROOT_REPORT_GEN)

try:
    from app.core.config import settings
except ImportError as e:
    class MockSettings:
        DASHSCOPE_API_KEY = None
        TEXT_MODEL = "qwen-plus"
        REPORT_PROMPT_TEMPLATE = None
        APP_NAME = "FallbackApp"
    settings = MockSettings()
    print(f"警告: 无法在 report_generator.py 中导入 app.core.config.settings: {e}", file=sys.stderr)


# Get the logger instance setup in app.py or utils.py
logger = logging.getLogger(settings.APP_NAME)
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class ReportGenerator:
    def __init__(self, config):
        """Initializes ReportGenerator with configuration and explicit safe headers."""
        self.config = config # Store config if needed elsewhere
        # 从 settings 获取 API Key 和模型名称
        self.api_key = settings.DASHSCOPE_API_KEY
        if not self.api_key:
            logger.error("CRITICAL: API Key not found in settings for ReportGenerator.")
            raise ValueError("API Key missing for ReportGenerator.")

        self.model = settings.TEXT_MODEL # 从 settings 获取文本模型
        self.base_url = config.get("base_url", "https://dashscope.aliyuncs.com/compatible-mode/v1")

        # --- Explicitly set safe default headers ---
        safe_headers = {
            "User-Agent": "MyPsychologyApp-ReportGenerator/1.0",
            "Accept": "application/json",
        }

        try:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                default_headers=safe_headers
            )
            logger.info(f"ReportGenerator OpenAI client initialized. Base URL: {self.base_url}. Using explicit safe headers.")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client in ReportGenerator: {e}", exc_info=True)
            raise

        # --- Default prompt template definition (moved inside init for clarity) ---
        self.default_prompt_template = """
请根据以下信息生成一份详细的心理分析报告，服务于警务工作场景。

**I. 被测者基础信息:**
姓名: {subject_info[name]}
性别: {subject_info[gender]}
身份证号: {subject_info[id_card]}
年龄: {subject_info[age]}
职业: {subject_info[occupation]}
案件名称: {subject_info[case_name]}
案件类型: {subject_info[case_type]}
人员身份: {subject_info[identity_type]}
人员类型: {subject_info[person_type]}
婚姻状况: {subject_info[marital_status]}
子女情况: {subject_info[children_info]}
有无犯罪前科: {criminal_record_text}
健康情况: {subject_info[health_status]}
手机号: {subject_info[phone_number]}
归属地: {subject_info[domicile]}

**II. 绘画分析 (基于AI对图片的描述):**
{description}

**III. 量表分析:**
量表类型: {questionnaire_type}
量表得分: {score}
量表答案详情 (JSON):
{questionnaire}
初步解释: {scale_interpretation}

**IV. 综合心理状态分析与建议:**
请结合以上所有信息（基础信息、绘画分析、量表结果），进行深入的心理状态评估，提取关键人格特征，并针对警务工作场景（如未成年人犯罪预防、在押人员管理、上访户调解、民辅警关怀等，根据人员类型判断侧重点）给出具体的风险评估、干预建议或沟通策略。分析需专业、客观、有条理。报告应直接开始分析内容，无需重复引言。

--- 分析报告正文 ---
"""
        # Use template from config if provided and is a string, otherwise use the default
        # 从 settings 中获取 REPORT_PROMPT_TEMPLATE
        config_template = settings.REPORT_PROMPT_TEMPLATE if hasattr(settings, 'REPORT_PROMPT_TEMPLATE') else None
        if isinstance(config_template, str) and config_template.strip():
            self.prompt_template = config_template
            logger.debug("Using prompt template from settings.")
        else:
            if config_template is not None:
                logger.warning("REPORT_PROMPT_TEMPLATE in settings is not a valid string. Using default.")
            else:
                logger.debug("REPORT_PROMPT_TEMPLATE not found in settings. Using default.")
            self.prompt_template = self.default_prompt_template


    # 确保 generate_report 方法也正确包含 self 和所有需要的参数
    def generate_report(self, description, questionnaire, subject_info, questionnaire_type, score, scale_interpretation):
        """Generates the report by formatting the prompt and calling the LLM API."""
        logger.info(f"Generating report for subject: {subject_info.get('name', 'N/A')}")

        # --- 在这里计算 criminal_record_text ---
        criminal_record_text = '是' if subject_info.get('criminal_record', 0) == 1 else '否'
        # ------------------------------------

        # Safely format questionnaire data (which should be a dictionary passed from ai_utils)
        questionnaire_str = "N/A"
        if questionnaire and isinstance(questionnaire, dict): # Check if it's a dict
            try:
                # Dump the dictionary to a pretty JSON string for the prompt
                questionnaire_str = json.dumps(questionnaire, ensure_ascii=False, indent=2)
            except Exception as json_err:
                logger.warning(f"Could not dump questionnaire dict to JSON: {json_err}. Using raw dict string.")
                questionnaire_str = str(questionnaire) # Fallback
        elif isinstance(questionnaire, str): # If it's already a string (e.g., JSON string)
            questionnaire_str = questionnaire
        elif questionnaire:
            logger.warning(f"Unexpected type for questionnaire data: {type(questionnaire)}. Using raw string.")
            questionnaire_str = str(questionnaire)


        # --- 构建 prompt_context，包含所有模板需要的键 ---
        prompt_context = {
            'description': description if description else "无",
            'questionnaire': questionnaire_str, # Use formatted string
            'subject_info': subject_info if subject_info else {}, # Ensure it's a dict
            'questionnaire_type': questionnaire_type if questionnaire_type else "未知",
            'score': score if score is not None else "N/A",
            'scale_interpretation': scale_interpretation if scale_interpretation else "无",
            'criminal_record_text': criminal_record_text # <--- 添加计算出的文本
        }
        # ---------------------------------------------

        # Ensure all required keys for the template exist in subject_info context
        default_keys = ["name", "gender", "id_card", "age", "occupation", "case_name", "case_type", "identity_type", "person_type", "marital_status", "children_info", "criminal_record", "health_status", "phone_number", "domicile"]
        # Ensure subject_info itself is a dict before iterating
        if isinstance(prompt_context['subject_info'], dict):
            for key in default_keys:
                prompt_context['subject_info'].setdefault(key, '未提供') # Set default if key missing
        else: # If subject_info is somehow not a dict, create a default one
            logger.warning(f"subject_info was not a dictionary (type: {type(prompt_context['subject_info'])}). Creating default context.")
            prompt_context['subject_info'] = {key: '未提供' for key in default_keys}


        try:
            # --- 使用 self.prompt_template 和构建好的 context 格式化 ---
            final_prompt = self.prompt_template.format(**prompt_context)
            logger.debug(f"Formatted Prompt (first 500 chars): {final_prompt[:500]}...")
        except KeyError as e:
            logger.error(f"Prompt template formatting error: Missing key {e}. Context keys available: {list(prompt_context.keys())}", exc_info=True)
            # Check if the missing key is expected in subject_info
            if str(e).strip("'") in default_keys:
                logger.error(f"Missing key '{e}' likely expected within subject_info dictionary: {prompt_context.get('subject_info')}")
            raise KeyError(f"Prompt template formatting error: Missing key {e}") from e
        except Exception as e_fmt:
            logger.error(f"Prompt template formatting error: {e_fmt}", exc_info=True)
            raise Exception(f"Prompt template formatting error: {e_fmt}") from e_fmt


        messages = [
            # Refined system prompt
            {"role": "system", "content": "你是一位专业的心理分析师。请根据用户提供的多维度信息（基础信息、绘画描述、量表结果与解释），结合心理学知识和警务场景，生成一份结构清晰、分析深入、建议具体的综合心理评估报告。"},
            {"role": "user", "content": final_prompt}
        ]

        try:
            logger.debug(f"Calling text model '{self.model}'...")
            completion = self.client.chat.completions.create(
                model=self.model, # 使用 self.model
                messages=messages,
            )
            report_content = completion.choices[0].message.content
            logger.info("Report content received successfully.")
            return report_content
        except Exception as e:
            logger.error(f"Error calling text generation API: {type(e).__name__} - {e}", exc_info=True)
            raise Exception(f"调用大模型 API 时出错 - {str(e)}") from e