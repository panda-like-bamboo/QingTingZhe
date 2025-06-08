# FILE: src/guidance_generator.py (修正版)
import logging
from typing import Optional, Dict, Any # <--- 添加 Any 导入
from openai import OpenAI
import os
import sys # 添加sys导入

# --- 导入 settings ---
# 确保路径正确，以便能够导入 settings
SRC_DIR_GUIDANCE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT_GUIDANCE = os.path.dirname(SRC_DIR_GUIDANCE) # PsychologyAnalysis/
if PROJECT_ROOT_GUIDANCE not in sys.path:
    sys.path.insert(0, PROJECT_ROOT_GUIDANCE)

try:
    from app.core.config import settings
except ImportError as e:
    # 如果无法导入 settings，则使用一个默认的空对象来避免崩溃
    class MockSettings:
        DASHSCOPE_API_KEY = None
        APP_NAME = "FallbackApp"
    settings = MockSettings()
    print(f"警告: 无法在 guidance_generator.py 中导入 app.core.config.settings: {e}", file=sys.stderr)

# --- 获取 logger 和配置 ---
logger = logging.getLogger(settings.APP_NAME) # 使用统一的 APP_NAME
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# --- AI 客户端初始化 ---
DASHSCOPE_API_KEY_GUIDANCE = settings.DASHSCOPE_API_KEY # 从 settings 获取
if not DASHSCOPE_API_KEY_GUIDANCE:
    logger.error("CRITICAL: Dashscope API Key 未配置，指导方案生成功能将失败！")

ai_client = None
if DASHSCOPE_API_KEY_GUIDANCE:
    try:
        safe_headers = {
            "User-Agent": "MyPsychologyApp-GuidanceGenerator/1.0",
            "Accept": "application/json",
        }
        ai_client = OpenAI(
            api_key=DASHSCOPE_API_KEY_GUIDANCE,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            default_headers=safe_headers
        )
        logger.info("Guidance Generator AI client initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI client for Guidance Generator: {e}", exc_info=True)
        ai_client = None

# --- 指导方案 Prompt 设计 (保持不变) ---
PROMPT_TEMPLATES: Dict[str, str] = {
    "petitioner": """
    **任务:** 你是一位经验丰富的警务心理疏导专家。请基于以下心理评估报告，为该上访户制定一份简洁、实用、具有针对性的情绪疏导与沟通建议方案。方案应侧重于理解其核心诉求背后的心理动机，识别潜在的情绪风险点，并提供具体的沟通技巧和安抚策略，旨在缓和其激动情绪，建立信任，引导其理性表达诉求。请直接输出疏导方案内容。

    **心理评估报告摘要:**
    ```
    {report_text}
    ```

    **情绪疏导与沟通建议方案:**
    """,

    "juvenile": """
    **任务:** 你是一位青少年心理辅导专家，专长于未成年人行为矫正与心理成长。请根据下方提供的心理评估报告，为这名未成年人设计一份初步的心理辅导概要方案。方案应关注报告中揭示的风险因素和保护性因素，提出符合其年龄特点的干预目标和策略，例如提升自我认知、情绪管理能力、社交技能、家庭关系改善等。请着重考虑预防其再次触犯法律的可能性。请直接输出辅导方案概要。

    **心理评估报告摘要:**
    ```    {report_text}
    ```

    **未成年人心理辅导方案概要:**
    """,

    "police": """
    **任务:** 你是一位专门为警务人员提供心理支持的专家。请分析以下民（辅）警的心理评估报告，并据此提供一份保密、实用、富有同理心的心理调适与关怀建议。建议应聚焦于报告中反映出的压力来源、潜在的职业倦怠风险或心理困扰，提出具体的自我调适方法（如压力应对技巧、情绪调节练习）、寻求支持的途径（如内部心理服务、外部资源）以及组织层面可以提供的关怀措施建议。请直接输出调适与关怀建议。

    **心理评估报告摘要:**
    ```
    {report_text}
    ```

    **民（辅）警心理调适与关怀建议:**
    """
}

def generate_guidance(report_text: str, scenario: str, model_name: str = "qwen-plus") -> Optional[str]:
    """
    根据评估报告和场景生成指导方案。

    Args:
        report_text (str): 评估报告的核心内容。
        scenario (str): 场景类型 ('petitioner', 'juvenile', 'police')。
        model_name (str): 使用的 Dashscope 模型。

    Returns:
        Optional[str]: 生成的指导方案文本，或在错误时返回包含错误信息的字符串。
    """
    global logger, ai_client # 引用全局（模块级）变量

    logger.info(f"Guidance Gen: 开始为场景 '{scenario}' 生成指导方案")
    if ai_client is None:
        logger.error("Guidance Gen: AI 客户端未初始化，无法生成指导方案。")
        return f"错误：AI 服务未配置，无法生成场景 '{scenario}' 的指导方案。"

    if scenario not in PROMPT_TEMPLATES:
        logger.error(f"Guidance Gen: 未知的指导方案场景类型: '{scenario}'")
        return f"错误：未知的指导方案场景类型 '{scenario}'。"

    # 格式化 Prompt
    try:
        prompt = PROMPT_TEMPLATES[scenario].format(report_text=report_text)
    except KeyError as e:
        logger.error(f"Guidance Gen: Prompt 模板格式化错误，缺少键 '{e}'。模板: {PROMPT_TEMPLATES[scenario][:100]}...")
        return f"错误：内部模板格式错误，无法生成场景 '{scenario}' 的指导方案。"
    except Exception as fmt_e:
        logger.error(f"Guidance Gen: Prompt 格式化时发生意外错误: {fmt_e}", exc_info=True)
        return f"错误：准备请求时出错，无法生成场景 '{scenario}' 的指导方案。"


    messages = [
        # 可以添加一个通用的 System Prompt
        {"role": "system", "content": "你是一位专业的心理与策略顾问，请根据提供的报告和任务要求，生成具体、可行的建议方案。"},
        {"role": "user", "content": prompt}
    ]

    try:
        logger.debug(f"Guidance Gen: 调用模型 '{model_name}'，场景: {scenario}")
        completion = ai_client.chat.completions.create(
            model=model_name,
            messages=messages,
            max_tokens=1000, # 允许生成较长的方案
            temperature=0.7 # 允许一定的创造性
        )
        # 检查是否有有效的响应内容
        if completion.choices and completion.choices[0].message and completion.choices[0].message.content:
            guidance_text = completion.choices[0].message.content.strip()
            if not guidance_text:
                logger.warning(f"Guidance Gen: 模型返回空内容，场景: {scenario}")
                return "AI 未能生成有效的指导方案。" # 返回提示信息
            logger.info(f"Guidance Gen: 成功为场景 '{scenario}' 生成指导方案。")
            return guidance_text
        else:
            logger.error(f"Guidance Gen: 模型响应无效或内容为空，场景: {scenario}。响应对象: {completion}")
            return "错误：AI 模型返回了无效的响应。"

    except Exception as e:
        logger.error(f"Guidance Gen: 调用 AI 模型时出错 (场景: {scenario}): {e}", exc_info=True)
        return f"错误：生成指导方案时发生错误 ({type(e).__name__})"