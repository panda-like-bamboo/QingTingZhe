#评估提交相关
# app/schemas/assessment.py
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime

# --- 用于 POST /api/assessments/submit 的请求体 (部分数据将来自 Form) ---
# Pydantic 模型通常用于 JSON body，但 FastAPI 也能从 Form 字段映射
# 这里定义基础信息字段，方便验证和文档化，实际接收用 Form(...)
class BasicInfoSubmit(BaseModel):
    name: str = Field(..., description="姓名")
    gender: str = Field(..., description="性别")
    id_card: Optional[str] = Field(None, description="身份证号")
    age: int = Field(..., gt=0, description="年龄")
    occupation: Optional[str] = Field(None, description="职业")
    case_name: Optional[str] = Field(None, description="案件名称")
    case_type: Optional[str] = Field(None, description="案件类型")
    identity_type: Optional[str] = Field(None, description="人员身份")
    person_type: Optional[str] = Field(None, description="人员类型")
    marital_status: Optional[str] = Field(None, description="婚姻状况")
    children_info: Optional[str] = Field(None, description="子女情况")
    criminal_record: Optional[int] = Field(0, ge=0, le=1, description="有无犯罪前科 (0:无, 1:有)")
    health_status: Optional[str] = Field(None, description="健康情况")
    phone_number: Optional[str] = Field(None, description="手机号")
    domicile: Optional[str] = Field(None, description="归属地")
    # 注意：scale_type 和 scale_answers 会作为独立的 Form 字段传入

# --- 用于 POST /api/assessments/submit 的响应 ---
class AssessmentSubmitResponse(BaseModel):
    status: str = "success" # "success" or "error"
    message: str
    submission_id: Optional[int] = None # 成功时返回 ID
    
class AssessmentSummary(BaseModel):
    """用于在列表中显示的评估摘要信息"""
    id: int
    subject_name: Optional[str] = None
    questionnaire_type: Optional[str] = None
    status: str
    created_at: datetime
    submitter_id: Optional[int] = None # 关联提交者ID

    class Config:
        from_attributes = True