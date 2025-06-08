# app/core/security.py
from datetime import datetime, timedelta, timezone
from typing import Any, Union, Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.core.config import settings
from app.schemas.token import TokenData # 导入令牌数据模式

# 使用 bcrypt 哈希算法
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = settings.ALGORITHM
SECRET_KEY = settings.SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证明文密码与哈希密码是否匹配"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """生成密码的哈希值"""
    return pwd_context.hash(password)

def create_access_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """创建 JWT 访问令牌"""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # 使用配置中的过期时间
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    # 令牌中至少包含过期时间和主题 (subject, 通常是用户名)
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[TokenData]:
    """解码访问令牌，验证其有效性"""
    try:
        # 解码 JWT
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # 提取用户名
        username: str | None = payload.get("sub")
        if username is None:
            # 令牌中没有 'sub' 字段
            return None
        # 你可以在这里添加更多的载荷验证逻辑 (例如：检查 scopes)
        # 返回包含用户名的 TokenData 对象
        return TokenData(username=username)
    except JWTError:
        # 令牌无效 (格式错误、签名不匹配、已过期等)
        return None