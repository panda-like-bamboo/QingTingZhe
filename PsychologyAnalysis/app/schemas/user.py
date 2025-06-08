# FILE: app/schemas/user.py (添加 UserUpdateAdmin 和 UserListResponse)
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List # 添加 List 导入

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: Optional[EmailStr] = Field(None, description="邮箱")
    full_name: Optional[str] = Field(None, max_length=100, description="全名")
    # 允许创建/更新时指定，但如果未指定，CRUD 层会使用默认值
    is_active: Optional[bool] = Field(True, description="是否激活")
    is_superuser: Optional[bool] = Field(False, description="是否超级用户")

class UserCreate(UserBase):
    password: str = Field(..., min_length=6, description="登录密码 (明文)")

class UserUpdate(UserBase):
    password: Optional[str] = Field(None, min_length=6, description="新密码 (可选，用于用户自我更新)")
    # 用户自我更新时不应能修改 is_active 和 is_superuser
    is_active: Optional[bool] = Field(None, description="不允许用户自我修改") # 阻止用户自己设置
    is_superuser: Optional[bool] = Field(None, description="不允许用户自我修改") # 阻止用户自己设置


# +++ 新增：管理员更新用户时使用的 Schema +++
class UserUpdateAdmin(BaseModel):
    """管理员更新用户信息时使用，允许修改激活和超管状态，密码可选"""
    email: Optional[EmailStr] = Field(None, description="新邮箱 (可选)")
    full_name: Optional[str] = Field(None, max_length=100, description="新全名 (可选)")
    is_active: Optional[bool] = Field(None, description="设置激活状态 (可选)") # 允许管理员修改
    is_superuser: Optional[bool] = Field(None, description="设置超级用户状态 (可选)") # 允许管理员修改
    password: Optional[str] = Field(None, min_length=6, description="设置新密码 (可选)")

class UserInDBBase(UserBase):
    id: int
    class Config:
        from_attributes = True # Pydantic V2 风格

class User(UserInDBBase):
    """用于 API 响应的用户模型 (不含密码)"""
    pass

# +++ 新增：用户列表响应 Schema +++
class UserListResponse(BaseModel):
    """用户列表接口的响应结构"""
    total: int = Field(..., description="符合条件的用户总数")
    users: List[User] = Field(..., description="当前页的用户列表")

# 内部数据库表示（通常不在 API 中直接暴露）
class UserInDB(UserInDBBase):
    hashed_password: str