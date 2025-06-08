# 文件路径: PsychologyAnalysis/app/routers/auth.py (最终修复版)
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

# --- 核心应用导入 ---
from app.core.config import settings
from app.core import security
from app import crud, models, schemas
from app.core.deps import get_db, get_current_active_user

# --- 日志设置 ---
logger = logging.getLogger(settings.APP_NAME)
router = APIRouter(
    # [->] 核心修复：确保前缀只包含模块自身路径，不含 /api/v1
    prefix="/auth",
    tags=["认证 (Authentication)"]
)

@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    OAuth2 兼容的令牌登录，为将来的请求获取访问令牌。
    """
    logger.info(f"收到登录请求，用户名: {form_data.username}")
    
    user = await crud.user.authenticate(
        db, username=form_data.username, password=form_data.password
    )
    
    if not user:
        logger.warning(f"为用户 '{form_data.username}' 登录失败：用户名或密码不正确。")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码不正确",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        logger.warning(f"非活动用户尝试登录: {form_data.username}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该用户已被禁用")

    access_token = security.create_access_token(subject=user.username)
    logger.info(f"用户 '{form_data.username}' 登录成功，已颁发令牌。")
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
async def register_user(
    *,
    db: AsyncSession = Depends(get_db),
    user_in: schemas.UserCreate = Body(...)
):
    """
    创建新用户。
    """
    logger.info(f"收到注册请求，用户名: {user_in.username}")
    
    existing_user = await crud.user.get_user_by_username(db, username=user_in.username)
    if existing_user:
        logger.warning(f"用户名 '{user_in.username}' 已被注册。")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已被注册",
        )
        
    if user_in.email:
        existing_email = await crud.user.get_user_by_email(db, email=user_in.email)
        if existing_email:
            logger.warning(f"邮箱 '{user_in.email}' 已被注册。")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该邮箱已被注册",
            )
            
    try:
        user = await crud.user.create_user(db=db, user_in=user_in)
        logger.info(f"用户 '{user.username}' (ID: {user.id}) 注册成功。")
        return user
    except IntegrityError: 
        await db.rollback()
        logger.error(f"为 {user_in.username} 注册时发生数据库完整性错误。", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="用户名或邮箱可能已被注册，请更换后重试。",
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"为 {user_in.username} 注册时发生未知错误: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注册过程中发生内部错误。",
        )

# [->] 路径修正：此路由将通过 /api/v1/auth/users/me 访问
@router.get("/users/me", response_model=schemas.User)
async def read_users_me(
    current_user: models.User = Depends(get_current_active_user)
):
    """
    获取当前登录用户的详细信息。
    """
    return current_user