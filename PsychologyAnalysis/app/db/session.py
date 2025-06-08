# app/db/session.py
import logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings # 导入你的设置

logger = logging.getLogger(settings.APP_NAME) # Or use a specific logger

# --- Asynchronous Database Engine ---
# Create an asynchronous engine using the DATABASE_URL from settings.
# Ensure settings.DATABASE_URL is like "sqlite+aiosqlite:///path/to/your.db"
logger.info(f"Creating async engine for database: {settings.DATABASE_URL}")
try:
    async_engine = create_async_engine(
        settings.DATABASE_URL,
        # echo=True,  # Uncomment for debugging SQL statements
        future=True  # Enables SQLAlchemy 2.0 style features
        # connect_args can be added here if needed, but typically not for aiosqlite
    )
    logger.info("Async engine created successfully.")
except Exception as e:
    logger.critical(f"Failed to create async engine: {e}", exc_info=True)
    raise e # Re-raise the exception to stop application startup if engine fails

# --- Asynchronous Database Session Maker ---
# Create an asynchronous session factory configured to use the async engine.
# expire_on_commit=False is recommended for FastAPI dependency usage,
# preventing attributes from being expired after commit within a request.
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,       # Specify the use of AsyncSession
    expire_on_commit=False,    # Keep objects accessible after commit within the session scope
    autocommit=False,          # Standard setting, commits are manual
    autoflush=False            # Standard setting, flushing is manual or on commit
)
logger.info("AsyncSessionLocal (async session maker) configured.")

# Note: You will typically use this AsyncSessionLocal in your dependency
# injection function (e.g., get_db in deps.py) to get session instances.