# app/db/init_db.py (使用 run_sync 修正)
import logging
import asyncio  # 1. 导入 asyncio 库
from app.db.session import async_engine # 确保你导入的是 async_engine
# 导入所有需要创建表的模型，以及 Base
from app.db.base_class import Base
from app.models.user import User # 导入 User 模型
# from app.models.assessment import Assessment # 如果有其他模型，也导入

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 2. 将 init_db 函数改为异步函数 (async def)
async def init_db() -> None:
    """
    根据 SQLAlchemy 模型异步地创建数据库表。
    """
    logger.info("Attempting to create database tables asynchronously...")
    try:
        # 3. 使用异步上下文管理器获取连接
        async with async_engine.begin() as conn:
            logger.info("Acquired async connection. Running create_all synchronously...")
            # 4. 在异步连接上，使用 run_sync 来执行同步的 create_all 方法
            # 这会将 create_all 的执行委托给事件循环的线程池
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Base.metadata.create_all executed via run_sync.")

        logger.info("Database tables created successfully (if they didn't exist).")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}", exc_info=True)
        raise e
    # finally:
        # 通常不需要手动 dispose，async with 会处理好连接释放
        # 如果需要确保引擎完全关闭（比如脚本结束时），可以取消注释下面两行
        # await async_engine.dispose()
        # logger.info("Async engine disposed.")

if __name__ == "__main__":
    print("Running database initialization...")
    # 5. 使用 asyncio.run() 来运行顶层的异步函数 init_db
    try:
        asyncio.run(init_db())
        print("Database initialization finished successfully.")
    except Exception as e:
        # 捕获在 init_db 中可能重新抛出的异常
        print(f"Database initialization failed: {e}")