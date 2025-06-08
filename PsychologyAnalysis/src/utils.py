# src/utils.py
import logging
import os
import sys
from logging.handlers import RotatingFileHandler # (可选) 使用轮转日志

# --------------------------------------------------------------------------
# 重要: 这个文件现在属于 'src' 包，
# 它将被 'app/main.py' 导入。
# 'app/main.py' 已经将项目根目录添加到了 sys.path,
# 所以这里理论上可以直接访问 'app' 包，但最好避免循环导入。
# 因此，日志配置的参数（如 level, dir）应该由调用者传入。
# --------------------------------------------------------------------------

# 获取项目根目录 (PsychologyAnalysis/)
# __file__ 指向当前文件 (utils.py)
# os.path.dirname(__file__) 指向 src 目录
# os.path.dirname(os.path.dirname(__file__)) 指向 PsychologyAnalysis 目录
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# 修改 setup_logging 函数，添加 log_dir_base_path 参数
def setup_logging(log_level_str: str = "INFO", log_dir_name: str = "logs", log_dir_base_path: str = None, logger_name: str = "QingtingzheApp"):
    """
    配置应用程序的日志记录。

    Args:
        log_level_str (str): 日志级别字符串 (e.g., "DEBUG", "INFO", "WARNING").
        log_dir_name (str): 日志文件夹的名称 (例如 'logs').
        log_dir_base_path (str, optional): 日志文件夹的基路径。如果提供，日志文件夹将是 `log_dir_base_path/log_dir_name`。
                                           如果未提供，则默认为 `PROJECT_ROOT/log_dir_name`。
        logger_name (str): 要配置的日志记录器的名称.
    """
    # --- 1. 获取日志级别 ---
    log_level = getattr(logging, log_level_str.upper(), logging.INFO)
    print(f"[Logging Setup] Setting log level to: {logging.getLevelName(log_level)} ({log_level_str})")

    # --- 2. 计算日志文件路径 ---
    # 根据 log_dir_base_path 确定日志目录
    if log_dir_base_path:
        log_directory = os.path.join(log_dir_base_path, log_dir_name)
    else:
        log_directory = os.path.join(PROJECT_ROOT, log_dir_name)

    try:
        os.makedirs(log_directory, exist_ok=True)
        print(f"[Logging Setup] Ensured log directory exists: {log_directory}")
    except OSError as e:
        print(f"[Logging Setup] Error creating log directory {log_directory}: {e}", file=sys.stderr)
        log_directory = None # 标记目录不可用

    log_file_path = os.path.join(log_directory, "app.log") if log_directory else None
    print(f"[Logging Setup] Log file path set to: {log_file_path}")


    # --- 3. 获取或创建 Logger 实例 ---
    logger = logging.getLogger(logger_name)
    logger.setLevel(log_level) # 设置 Logger 的基础级别

    # --- 4. 清除旧的 Handlers (防止重复添加) ---
    if logger.hasHandlers():
        print("[Logging Setup] Clearing existing handlers for logger:", logger_name)
        # 复制列表，因为在迭代时删除会出问题
        for handler in list(logger.handlers):
            logger.removeHandler(handler)
            handler.close() # 关闭 handler 释放资源

    # --- 5. 创建 Formatter ---
    log_format = "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
    formatter = logging.Formatter(log_format)

    # --- 6. 创建并添加 Handlers ---

    # a) 控制台 Handler (总是添加)
    console_handler = logging.StreamHandler(sys.stdout) # 输出到标准输出
    console_handler.setLevel(log_level) # 控制台 Handler 也遵循设定的级别
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    print(f"[Logging Setup] Added Console Handler (Level: {logging.getLevelName(console_handler.level)})")

    # b) 文件 Handler (如果路径有效)
    if log_file_path:
        try:
            file_handler = RotatingFileHandler(log_file_path, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8')
            file_handler.setLevel(log_level) # 文件 Handler 也遵循设定的级别
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            print(f"[Logging Setup] Added Rotating File Handler (Level: {logging.getLevelName(file_handler.level)})")
        except Exception as e:
            print(f"[Logging Setup] Failed to create/add file handler for {log_file_path}: {e}", file=sys.stderr)
            logger.error(f"Failed to set up file logging to {log_file_path}: {e}")

    # --- 7. (可选) 配置特定库的日志级别 ---
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING) # 减少SQLAlchemy的详细输出

    print(f"[Logging Setup] Configuration for logger '{logger_name}' complete.")