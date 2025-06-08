# 文件: app/schemas/encyclopedia.py
from pydantic import BaseModel
from typing import List, Optional

class EncyclopediaEntry(BaseModel):
    """单个百科条目的结构"""
    category: str
    title: str
    content: str

class CategoriesResponse(BaseModel):
    """获取分类列表的响应"""
    categories: List[str]

class EntriesResponse(BaseModel):
    """获取条目列表的响应"""
    entries: List[EncyclopediaEntry]
    # 可以添加分页信息 (如果需要)
    # total: Optional[int] = None
    # page: Optional[int] = None
    # size: Optional[int] = None

# 可以复用 EncyclopediaEntry 作为随机条目的响应，或者定义一个更简单的
# class RandomTipResponse(BaseModel):
#     tip: str