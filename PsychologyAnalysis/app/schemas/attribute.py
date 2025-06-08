# FILE: app/schemas/attribute.py
from pydantic import BaseModel, Field
from typing import Optional

class AttributeBase(BaseModel):
    """属性的基础模型，包含通用字段"""
    name: str = Field(..., max_length=100, description="属性名称 (e.g., 焦虑, 抑郁)")
    description: Optional[str] = Field(None, description="属性的详细描述")
    category: Optional[str] = Field(None, max_length=50, description="属性分类 (e.g., 情绪状态, 行为风险)")

class AttributeCreate(AttributeBase):
    """创建新属性时使用的模型"""
    pass # 继承 Base 即可

class AttributeUpdate(AttributeBase):
    """更新属性时使用的模型 (允许部分更新)"""
    name: Optional[str] = Field(None, max_length=100) # 更新时名称也可能可选

class AttributeRead(AttributeBase):
    """从数据库读取属性时使用的模型，包含 ID"""
    id: int

    class Config:
        from_attributes = True # Pydantic v2: orm_mode = True