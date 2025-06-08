# app/core/celery_app.py




from celery import Celery
from app.core.config import settings # 导入你的设置

# 配置 Redis 作为 Broker 和 Backend
# 使用 settings 中的配置或默认值
REDIS_URL = "redis://localhost:6379/0" # 默认 Redis 地址和数据库 0
# 你可以在 .env 中添加 REDIS_URL 并从 settings 加载

# 创建 Celery 实例
# main 参数通常是 Celery 应用的入口点名称，这里用 'app' 或项目名
celery_app = Celery(
    "QingtingzheApp", # 与 FastAPI app name 保持一致或自定义
    broker=REDIS_URL,
    backend=REDIS_URL, # 使用 Redis 作为结果存储后端
    include=['app.tasks.analysis'] # 指定包含任务定义的模块列表
)

# 可选：Celery 配置项 (可以放在 settings 或这里)
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],  # Allow json content
    result_serializer='json',
    timezone='Asia/Shanghai', # 设置时区
    enable_utc=True,
    # task_track_started=True, # 如果需要追踪任务开始状态
    # broker_connection_retry_on_startup=True, # 启动时自动重试连接 broker
)

# 可选: 打印确认信息
print(f"[Celery Setup] Celery app configured. Broker: {REDIS_URL}, Backend: {REDIS_URL}")
print(f"[Celery Setup] Included task modules: {celery_app.conf.include}")

# 如果你需要在任务中使用 FastAPI 的依赖项或设置，
# 可以考虑更复杂的设置，但现在保持简单。