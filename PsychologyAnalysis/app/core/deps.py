# FILE: app/core/deps.py (修改后，添加 get_current_active_superuser)
import logging
from typing import AsyncGenerator, Optional # Use AsyncGenerator for async yield
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession # Import AsyncSession

# --- Core App Imports ---
from app.core.config import settings
from app.core.security import decode_access_token # Your JWT decoding function

# --- Database and CRUD Imports ---
from app.db.session import AsyncSessionLocal # Import the async session maker
from app import crud, models, schemas # Adjust imports based on your project structure

logger = logging.getLogger(settings.APP_NAME) # Use the main app logger

# --- OAuth2 Scheme Definition ---
# Define the URL where clients will send username/password to get a token.
# This should match the path operation of your login endpoint.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token")

# --- Asynchronous Database Session Dependency ---
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides an asynchronous database session per request.
    It ensures the session is properly closed afterwards.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            # Optional: You could uncomment the next line if you want commits
            # to happen automatically at the end of successful requests,
            # but manual commits in CRUD functions are generally preferred
            # for better control.
            # await session.commit()
        except Exception as e:
            # Rollback in case of exceptions during the request handling
            logger.error(f"数据库会话错误: {e}", exc_info=True)
            await session.rollback()
            # Re-raise the exception so FastAPI can handle it
            raise
        # Session is automatically closed when exiting the 'async with' block

# --- Asynchronous Current User Dependency ---
async def get_current_user(
    db: AsyncSession = Depends(get_db),          # Depend on the async get_db
    token: str = Depends(oauth2_scheme)          # Get token from Authorization header
) -> models.User:                                # Return the SQLAlchemy User model
    """
    Decodes the JWT token, validates it, and retrieves the current user
    from the database asynchronously. Raises HTTPException if invalid.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据", # "Could not validate credentials"
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Decode the token using your security utility
    token_data = decode_access_token(token)
    if token_data is None or token_data.username is None:
        logger.warning("Token 解码失败或 Token 负载中缺少用户名。")
        raise credentials_exception

    # Retrieve the user from the database asynchronously using the async CRUD function
    try:
        # Ensure crud.user.get_user_by_username is an async function
        user = await crud.user.get_user_by_username(db, username=token_data.username)
    except Exception as e:
        logger.error(f"获取用户 '{token_data.username}' 时发生数据库错误: {e}", exc_info=True)
        # Don't expose internal DB errors directly, raise the standard credentials exception
        raise credentials_exception

    if user is None:
        logger.warning(f"用户 '{token_data.username}' 在 Token 中找到但在数据库中未找到。")
        raise credentials_exception

    # Return the validated user object
    return user

# --- Asynchronous Active User Dependency ---
async def get_current_active_user(
    current_user: models.User = Depends(get_current_user), # Depend on get_current_user
) -> models.User:
    """
    Ensures the user retrieved from the token is marked as active.
    """
    if not current_user.is_active:
        logger.warning(f"非活动用户尝试认证: {current_user.username}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="非活动用户") # "Inactive user"
    return current_user

# +++ 新增：超级用户依赖项 +++
async def get_current_active_superuser(
    current_user: models.User = Depends(get_current_active_user), # 首先确保用户是活动的
) -> models.User:
    """
    确保当前用户是活动的 **并且** 是超级用户。
    如果不是超级用户，则引发 HTTPException。
    此依赖项应用于所有需要管理员权限的接口。
    """
    if not current_user.is_superuser:
        logger.warning(f"非超级用户拒绝访问管理接口: {current_user.username}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, # 403 Forbidden 表示权限不足
            detail="用户权限不足", # "The user doesn't have enough privileges"
        )
    # 如果检查通过，记录调试信息并返回用户对象
    logger.debug(f"超级用户访问已授权: {current_user.username}")
    return current_user