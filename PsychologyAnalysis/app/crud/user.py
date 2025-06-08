# 文件路径: PsychologyAnalysis/app/crud/user.py

import logging
from typing import Tuple, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

# --- 核心应用导入 ---
from app.core.security import get_password_hash, verify_password
from app.core.config import settings
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserUpdateAdmin

# --- 日志设置 ---
logger = logging.getLogger(settings.APP_NAME)


# --- 用户认证 ---

async def authenticate(db: AsyncSession, *, username: str, password: str) -> Optional[User]:
    """
    通过用户名和密码对用户进行身份验证。
    这是登录流程的核心数据库操作。

    Args:
        db (AsyncSession): 数据库会话。
        username (str): 需要认证的用户名。
        password (str): 用户提供的明文密码。

    Returns:
        Optional[User]: 如果认证成功，返回 User ORM 对象；否则返回 None。
    """
    logger.debug(f"CRUD: 正在尝试认证用户 '{username}'")
    
    # 步骤1: 根据用户名查找用户
    user = await get_user_by_username(db, username=username)
    if not user:
        logger.debug(f"CRUD: 认证失败，用户 '{username}' 未在数据库中找到。")
        return None
        
    # 步骤2: 验证密码是否匹配
    if not verify_password(password, user.hashed_password):
        logger.debug(f"CRUD: 认证失败，用户 '{username}' 的密码不正确。")
        return None
        
    logger.debug(f"CRUD: 用户 '{username}' 认证成功。")
    return user


# --- 用户查询 (Getters) ---

async def get_user(db: AsyncSession, user_id: int) -> Optional[User]:
    """根据用户ID异步获取单个用户。"""
    result = await db.execute(select(User).filter(User.id == user_id))
    return result.scalar_one_or_none()

async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    """根据用户名异步获取单个用户，用于登录和注册检查。"""
    result = await db.execute(select(User).filter(User.username == username))
    return result.scalar_one_or_none()

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """根据邮箱异步获取单个用户，用于注册时检查邮箱是否已被使用。"""
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalar_one_or_none()

async def get_users(db: AsyncSession, skip: int = 0, limit: int = 100) -> Tuple[List[User], int]:
    """
    分页获取用户列表以及用户总数。
    主要用于后台管理界面。

    Args:
        db (AsyncSession): 数据库会话。
        skip (int): 跳过的记录数。
        limit (int): 返回的最大记录数。

    Returns:
        Tuple[List[User], int]: 一个包含用户列表和总用户数的元组。
    """
    # 查询指定范围的用户列表
    stmt_users = select(User).offset(skip).limit(limit).order_by(User.id)
    result_users = await db.execute(stmt_users)
    users = list(result_users.scalars().all())
    
    # 查询用户总数，用于前端分页计算
    stmt_count = select(func.count()).select_from(User)
    result_count = await db.execute(stmt_count)
    total_count = result_count.scalar_one()
    
    return users, total_count


# --- 用户创建与更新 (Create/Update) ---

async def create_user(db: AsyncSession, *, user_in: UserCreate) -> User:
    """
    异步创建新用户。

    Args:
        db (AsyncSession): 数据库会话。
        user_in (UserCreate): 包含新用户信息的Pydantic模型。

    Returns:
        User: 创建成功后的 User ORM 对象。
    """
    # 将明文密码哈希化处理，确保数据库中不存储明文密码
    hashed_password = get_password_hash(user_in.password)
    
    # 创建User模型实例
    db_user = User(
        username=user_in.username,
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=hashed_password,
        is_active=user_in.is_active,
        is_superuser=user_in.is_superuser,
    )
    
    # 将新用户添加到会话、提交到数据库并刷新以获取ID等信息
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    
    return db_user

async def update_user(db: AsyncSession, *, db_user: User, user_in: UserUpdate) -> User:
    """
    异步更新普通用户信息（通常由用户自己操作）。

    Args:
        db (AsyncSession): 数据库会话。
        db_user (User): 从数据库中获取的、要被更新的User对象。
        user_in (UserUpdate): 包含待更新字段的Pydantic模型。

    Returns:
        User: 更新后的 User ORM 对象。
    """
    # model_dump(exclude_unset=True) 仅包含在请求中明确提供的字段
    update_data = user_in.model_dump(exclude_unset=True)
    
    # 如果请求中包含密码，则进行哈希处理并更新
    if "password" in update_data and update_data["password"]:
        hashed_password = get_password_hash(update_data["password"])
        db_user.hashed_password = hashed_password
    
    # 遍历其他字段并更新
    for field, value in update_data.items():
        if field != "password":
            setattr(db_user, field, value)
            
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    
    return db_user

async def update_user_admin(db: AsyncSession, *, db_user: User, user_in: UserUpdateAdmin) -> User:
    """
    异步更新用户信息（由管理员操作，权限更高）。

    Args:
        db (AsyncSession): 数据库会话。
        db_user (User): 要被更新的User对象。
        user_in (UserUpdateAdmin): 包含待更新字段的管理员专用Pydantic模型。

    Returns:
        User: 更新后的 User ORM 对象。
    """
    # 逻辑与 update_user 类似，但使用 UserUpdateAdmin schema，可能包含更多可修改字段
    update_data = user_in.model_dump(exclude_unset=True)
    
    if "password" in update_data and update_data["password"]:
        hashed_password = get_password_hash(update_data["password"])
        db_user.hashed_password = hashed_password
        
    for field, value in update_data.items():
        if field != "password":
            setattr(db_user, field, value)
            
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    
    return db_user