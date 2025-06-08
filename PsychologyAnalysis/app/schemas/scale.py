# 量表相关
# app/schemas/scale.py
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class ScaleOption(BaseModel):
    """量表问题的选项"""
    text: str
    score: int | float # 分数可能是整数或浮点数

class ScaleQuestion(BaseModel):
    """量表问题结构"""
    number: int
    text: str
    options: List[ScaleOption]

class ScaleInfo(BaseModel):
    """量表基本信息 (用于列表显示)"""
    code: str # 量表代码 (e.g., 'SAS', 'Personality')
    name: str # 量表显示名称

# --- 用于 /api/scales/{scale_code}/questions 的响应 ---
class ScaleQuestionsResponse(BaseModel):
    questions: Optional[List[ScaleQuestion]] = None
    error: Optional[str] = None # 如果找不到问题，可以返回错误信息

# --- 用于 /api/scales 的响应 ---
class AvailableScalesResponse(BaseModel):
    scales: List[ScaleInfo]