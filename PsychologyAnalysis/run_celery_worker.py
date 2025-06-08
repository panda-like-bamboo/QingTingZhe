# run_celery_worker.py
import os
import sys

# --- 1. 定位项目根目录 ---
# __file__ 指向这个脚本文件 (run_celery_worker.py)
# os.path.dirname(__file__) 指向项目根目录 (PsychologyAnalysis/)
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
print(f"[Worker Start Script] Project Root detected: {PROJECT_ROOT}")

# --- 2. 将项目根目录添加到 sys.path ---
# 这样 Celery 启动时就能找到 app 和 src 包
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
    print(f"[Worker Start Script] Added {PROJECT_ROOT} to sys.path")
else:
    print(f"[Worker Start Script] {PROJECT_ROOT} already in sys.path")

# --- 3. 导入 Celery App 实例 ---
# 现在可以安全地导入了
try:
    from app.core.celery_app import celery_app
    print("[Worker Start Script] Successfully imported celery_app")
except ImportError as e:
    print(f"[Worker Start Script] CRITICAL ERROR: Could not import celery_app: {e}")
    print("Please ensure app/core/celery_app.py exists and dependencies are installed.")
    sys.exit(1)
except Exception as e:
     print(f"[Worker Start Script] CRITICAL ERROR during celery_app import: {e}")
     sys.exit(1)


# --- 4. (可选) 加载 .env 文件 (如果 Celery 任务需要直接访问环境变量) ---
# Celery worker 默认不一定加载 .env。如果你的任务代码 (如 ai_utils)
# 需要读取 .env 中的变量 (除了 Pydantic Settings 已经加载的)，
# 在这里加载它。
# from dotenv import load_dotenv
# dotenv_path = os.path.join(PROJECT_ROOT, '.env')
# if os.path.exists(dotenv_path):
#     load_dotenv(dotenv_path=dotenv_path)
#     print(f"[Worker Start Script] Loaded environment variables from: {dotenv_path}")
# else:
#     print("[Worker Start Script] .env file not found, skipping dotenv load.")


# --- 5. 准备 Celery Worker 的命令行参数 ---
# 你可以在这里定义参数，或者从命令行读取
worker_args = [
    'worker',             # 命令
    '--loglevel=info',    # 日志级别
    # '-P', 'solo',       # 在 Windows 上需要添加这个参数
    # '-c', '4',          # (可选) 并发数 (Linux/macOS)
    # '--pool=prefork',   # (可选) 进程池类型 (Linux/macOS 默认)
]

# --- 针对 Windows 添加 solo 进程池 ---
if sys.platform == "win32":
     if '-P' not in worker_args and '--pool' not in worker_args:
         print("[Worker Start Script] Windows detected, adding '-P solo' argument.")
         worker_args.extend(['-P', 'solo'])

# --- 6. 执行 Celery Worker 命令 ---
print(f"[Worker Start Script] Starting Celery worker with args: {worker_args}")
# 使用 celery_app.worker_main 来启动 worker，它会处理命令行参数
celery_app.worker_main(argv=worker_args)