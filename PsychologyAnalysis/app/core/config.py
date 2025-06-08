# 文件路径: PsychologyAnalysis/app/core/config.py

import os
import sys
import json
import yaml
import logging
import traceback
from typing import List, Union, Optional, Dict, Any
from pydantic_settings import BaseSettings, SettingsConfigDict

# --- 基本日志设置 (用于配置加载本身) ---
# 获取一个专门用于配置加载问题的基本日志记录器实例
# 这避免了主应用程序记录器尚未配置时可能出现的问题
config_logger = logging.getLogger("ConfigLoader")
# 如果主设置尚未运行，则设置默认级别
config_logger.setLevel(logging.INFO)
# 如果没有处理程序存在 (例如，直接运行脚本)，则添加一个处理程序
if not config_logger.hasHandlers():
    ch = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    config_logger.addHandler(ch)

# --- 项目路径计算 ---
# __file__ 指向此文件 (config.py)
# os.path.dirname(__file__) 指向 app/core
# os.path.join(os.path.dirname(__file__), "..", "..") 指向项目根目录 PsychologyAnalysis/
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CONFIG_YAML_PATH = os.path.join(PROJECT_ROOT, "config/config.yaml")
DOTENV_PATH = os.path.join(PROJECT_ROOT, ".env")
ENCYCLOPEDIA_JSON_PATH = os.path.join(PROJECT_ROOT, "config/psychology_encyclopedia.json")

class Settings(BaseSettings):
    """
    应用程序设置，从 .env 文件和 YAML 加载。
    对于重叠的变量，.env 文件具有优先权。
    """
    # --- 基本应用设置 ---
    APP_NAME: str = "Qingtingzhe AI Analysis"
    ENVIRONMENT: str = "development"
    API_V1_STR: str = "/api/v1"
    LOG_LEVEL: str = "INFO"

    # --- 安全设置 (JWT 认证) ---
    SECRET_KEY: str = "a_very_unsafe_default_secret_key_please_change_in_dotenv"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 默认令牌过期时间：7天

    # --- CORS (跨源资源共享) ---
    # 允许访问后端的源列表 (逗号分隔的字符串或 '*')
    # 示例: "http://localhost:8081,http://192.168.1.10:5173" 或 "*"
    BACKEND_CORS_ORIGINS_STR: str = "http://localhost:8081,http://127.0.0.1:8081,http://localhost:5173,http://127.0.0.1:5173,http://192.168.43.190:5173"

    # --- 数据库 ---
    DB_PATH_SQLITE: str = os.path.join(PROJECT_ROOT, "psychology_analysis.db")
    DATABASE_URL: str = f"sqlite+aiosqlite:///{DB_PATH_SQLITE}"

    # --- 文件存储 ---
    UPLOADS_DIR: str = os.path.join(PROJECT_ROOT, "uploads")
    LOGS_DIR: str = os.path.join(PROJECT_ROOT, "logs")

    # --- AI 服务 (Dashscope) API ---
    DASHSCOPE_API_KEY: Optional[str] = None

    # --- Redis 配置 (用于 Celery Broker 和 Backend) ---
    REDIS_URL: str = "redis://localhost:6379/0"

    # --- 从 config.yaml 加载的备选或默认值 ---
    TEXT_MODEL: str = "qwen-plus"
    VISION_MODEL: str = "qwen-vl-plus"
    REPORT_PROMPT_TEMPLATE: Optional[str] = None
    YAML_CONFIG: Dict[str, Any] = {}

    # --- 心理学百科全书 ---
    PSYCHOLOGY_ENCYCLOPEDIA_FILE: str = ENCYCLOPEDIA_JSON_PATH
    PSYCHOLOGY_ENTRIES: List[Dict[str, str]] = []

    # Pydantic Settings 配置
    model_config = SettingsConfigDict(
        env_file=DOTENV_PATH,
        extra='ignore'
    )

# --- 辅助函数 ---

def load_yaml_config(yaml_path: str) -> Dict[str, Any]:
    """从 YAML 文件加载配置。"""
    if not os.path.exists(yaml_path):
        config_logger.warning(f"在 {yaml_path} 未找到 YAML 配置文件。返回空配置。")
        return {}
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
            if config_data is None:
                config_logger.warning(f"位于 {yaml_path} 的 YAML 配置文件为空。返回空配置。")
                return {}
            config_logger.info(f"成功从 {yaml_path} 加载配置。")
            return config_data
    except Exception as e:
        config_logger.error(f"从 {yaml_path} 加载 YAML 配置时出错: {e}", exc_info=True)
        return {}

def load_encyclopedia_from_json(encyclopedia_path: str) -> List[Dict[str, str]]:
    """从 JSON 文件加载百科条目列表，并进行基本验证。"""
    if not os.path.exists(encyclopedia_path):
        config_logger.warning(f"百科文件未找到: {encyclopedia_path}。返回空列表。")
        return []
    try:
        with open(encyclopedia_path, 'r', encoding='utf-8') as f:
            entries_list = json.load(f)
            if not isinstance(entries_list, list):
                config_logger.error(f"百科文件 {encyclopedia_path} 格式错误，根元素不是列表。")
                return []
            valid_entries = []
            required_keys = {"category", "title", "content"}
            for i, entry in enumerate(entries_list):
                if isinstance(entry, dict) and required_keys.issubset(entry.keys()):
                    if all(isinstance(entry[key], str) and entry[key].strip() for key in required_keys):
                        valid_entries.append({key: entry[key].strip() for key in required_keys})
                    else:
                        config_logger.warning(f"百科文件 {encyclopedia_path} 中第 {i+1} 条记录的值无效(非字符串或为空)，已跳过。")
                else:
                    config_logger.warning(f"百科文件 {encyclopedia_path} 中第 {i+1} 条记录格式错误或缺少必需的键 ({required_keys})，已跳过。")
            config_logger.info(f"成功从 {encyclopedia_path} 加载 {len(valid_entries)} 条有效的百科条目。")
            return valid_entries
    except json.JSONDecodeError as e:
        config_logger.error(f"解析百科 JSON 文件 {encyclopedia_path} 时出错: {e}", exc_info=True)
        return []
    except Exception as e:
        config_logger.error(f"加载百科文件 {encyclopedia_path} 时发生意外错误: {e}", exc_info=True)
        return []

def parse_cors_origins(origins_str: str) -> List[str]:
    """将逗号分隔的源字符串解析为字符串列表，并支持通配符 '*'。"""
    if not origins_str or not isinstance(origins_str, str):
        default_origins = ["http://localhost:8081", "http://127.0.0.1:8081", "http://localhost:5173", "http://127.0.0.1:5173", "http://192.168.43.190:5173"]
        config_logger.warning(f"BACKEND_CORS_ORIGINS_STR 为空或无效 ('{origins_str}')。使用默认值: {default_origins}")
        return default_origins

    if origins_str.strip() == "*":
        config_logger.warning("CORS 配置为 '*'，将允许所有来源。这在开发中很方便，但在生产环境中应谨慎使用。")
        return ["*"]

    try:
        parsed = [origin.strip() for origin in origins_str.split(",") if origin.strip()]
        if not parsed:
             default_origins = ["http://localhost:8081", "http://127.0.0.1:8081", "http://localhost:5173", "http://127.0.0.1:5173", "http://192.168.43.190:5173"]
             config_logger.warning(f"解析 BACKEND_CORS_ORIGINS_STR '{origins_str}' 得到空列表。使用默认值: {default_origins}")
             return default_origins
        config_logger.info(f"成功解析 CORS 源: {parsed}")
        return parsed
    except Exception as e:
        default_origins = ["http://localhost:8081", "http://127.0.0.1:8081", "http://localhost:5173", "http://127.0.0.1:5173", "http://192.168.43.190:5173"]
        config_logger.error(f"解析 BACKEND_CORS_ORIGINS_STR '{origins_str}' 时出错: {e}。使用默认值: {default_origins}", exc_info=True)
        return default_origins


# --- 执行配置加载 ---

try:
    settings = Settings()
except Exception as e:
    config_logger.critical(f"在 Settings 初始化期间发生严重错误: {e}")
    traceback.print_exc()
    sys.exit(1)

if settings.SECRET_KEY == "a_very_unsafe_default_secret_key_please_change_in_dotenv":
    config_logger.critical("\n" + "="*80 + "\n" + " " * 25 + "关键安全警告\n" + "="*80 +
                         "\nSECRET_KEY 正在使用默认的不安全值！\n"
                         "请生成一个强密钥并将其设置在 .env 文件中。\n"
                         "示例生成命令: openssl rand -hex 32\n" + "="*80)

yaml_config_data = load_yaml_config(CONFIG_YAML_PATH)
settings.YAML_CONFIG = yaml_config_data

if settings.DASHSCOPE_API_KEY is None:
    yaml_api_key = yaml_config_data.get("api_key")
    if yaml_api_key:
        settings.DASHSCOPE_API_KEY = yaml_api_key
        config_logger.warning("从 YAML 加载了 DASHSCOPE_API_KEY (推荐使用 .env)。")

if settings.TEXT_MODEL == "qwen-plus":
    settings.TEXT_MODEL = yaml_config_data.get("text_model", settings.TEXT_MODEL)
if settings.VISION_MODEL == "qwen-vl-plus":
    settings.VISION_MODEL = yaml_config_data.get("vision_model", settings.VISION_MODEL)
if settings.REPORT_PROMPT_TEMPLATE is None:
    settings.REPORT_PROMPT_TEMPLATE = yaml_config_data.get("REPORT_PROMPT_TEMPLATE")

settings.PSYCHOLOGY_ENTRIES = load_encyclopedia_from_json(settings.PSYCHOLOGY_ENCYCLOPEDIA_FILE)
if not settings.PSYCHOLOGY_ENTRIES:
    config_logger.warning("未能加载任何心理百科条目，相关功能可能受影响。")

try:
    os.makedirs(settings.UPLOADS_DIR, exist_ok=True)
    os.makedirs(settings.LOGS_DIR, exist_ok=True)
    config_logger.info(f"确保目录存在: 上传='{settings.UPLOADS_DIR}', 日志='{settings.LOGS_DIR}'")
except OSError as e:
     config_logger.error(f"创建必要目录时出错: {e}", exc_info=True)

if not settings.DASHSCOPE_API_KEY:
    config_logger.critical("\n" + "="*80 + "\n" + " " * 28 + "关键配置缺失\n" + "="*80 +
                         "\nDASHSCOPE_API_KEY 未在 .env 或 config.yaml 中设置！\n"
                         "AI 相关功能将无法正常工作。\n"
                         "请在项目根目录的 .env 文件中添加一行: DASHSCOPE_API_KEY='你的密钥'\n" + "="*80)

parsed_cors_origins: List[str] = parse_cors_origins(settings.BACKEND_CORS_ORIGINS_STR)

config_logger.info("--- 最终生效的应用程序设置 ---")
config_logger.info(f"应用名称: {settings.APP_NAME}")
config_logger.info(f"运行环境: {settings.ENVIRONMENT}")
config_logger.info(f"日志级别: {settings.LOG_LEVEL}")
config_logger.info(f"API V1 前缀: {settings.API_V1_STR}")
config_logger.info(f"数据库路径: {settings.DB_PATH_SQLITE}")
config_logger.info(f"数据库 URL: {settings.DATABASE_URL}")
config_logger.info(f"Redis URL: {settings.REDIS_URL}")
config_logger.info(f"上传目录: {settings.UPLOADS_DIR}")
config_logger.info(f"日志目录: {settings.LOGS_DIR}")
config_logger.info(f"CORS 源 (已解析): {parsed_cors_origins}")
config_logger.info(f"JWT 算法: {settings.ALGORITHM}")
config_logger.info(f"令牌过期时间 (分钟): {settings.ACCESS_TOKEN_EXPIRE_MINUTES}")
config_logger.info(f"SECRET_KEY 已加载: {'是' if settings.SECRET_KEY != 'a_very_unsafe_default_secret_key_please_change_in_dotenv' else '否 (使用默认值 - 极不安全!)'}")
config_logger.info(f"DASHSCOPE_API_KEY 已加载: {'是' if settings.DASHSCOPE_API_KEY else '否 - 关键警告!'}")
config_logger.info(f"文本模型: {settings.TEXT_MODEL}")
config_logger.info(f"视觉模型: {settings.VISION_MODEL}")
config_logger.info(f"已加载百科条目数: {len(settings.PSYCHOLOGY_ENTRIES)}")
config_logger.info("------------------------------------")