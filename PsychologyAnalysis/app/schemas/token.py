# app/schemas/token.py
from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    """响应模型：登录成功后返回给客户端的令牌"""
    access_token: str
    token_type: str = "bearer" # 标准 OAuth2 类型

class TokenData(BaseModel):
    """内部模型：JWT 令牌载荷 (Payload) 的数据结构"""
    username: Optional[str] = None
    # 你未来可以在这里添加其他需要存储在令牌中的信息，
    # 例如用户 ID 或角色/权限 (scopes)
    # scopes: List[str] = []