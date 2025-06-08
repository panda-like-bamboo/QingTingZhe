# 文件路径: PsychologyAnalysis/app/schemas/guidance.py (请确认或替换)

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class AttributeRead(BaseModel):
    id: int
    name: str = Field(..., description="属性名称")
    class Config:
        from_attributes = True

class ReportDataForGuidance(BaseModel):
    id: int
    subject_name: Optional[str] = None
    report_text: Optional[str] = None
    created_at: Optional[Any] = None
    attributes: List[AttributeRead] = []
    class Config:
        from_attributes = True

# [->] 关键：我们定义的是这个名称
class GuidanceWithReportResponse(BaseModel):
    report: ReportDataForGuidance
    guidance: str
    error: Optional[str] = None
    class Config:
        from_attributes = True