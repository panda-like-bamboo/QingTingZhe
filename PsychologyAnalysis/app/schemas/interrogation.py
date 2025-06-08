# 文件路径: PsychologyAnalysis/app/schemas/interrogation.py

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class InterrogationBasicInfo(BaseModel):
    """审讯笔录 - 开始时输入的基础信息"""
    person_name: str = Field(..., description="被讯问人姓名")
    person_gender: Optional[str] = Field(None, description="性别")
    person_id_type_number: Optional[str] = Field(None, description="身份证号")
    person_address: Optional[str] = Field(None, description="家庭住址")
    person_contact: Optional[str] = Field(None, description="联系方式")
    person_age: Optional[int] = Field(None, description="年龄")
    is_minor: Optional[bool] = Field(None, description="是否未成年")
    person_dob: Optional[str] = Field(None, description="出生日期")
    person_hukou: Optional[str] = Field(None, description="户籍所在地")
    case_type: Optional[str] = Field(None, description="涉及案件类型")
    interrogation_location: Optional[str] = Field(None, description="讯问地点")
    interrogator_count: Optional[int] = Field(None, description="讯问人员数量")
    interrogator_ids: Optional[str] = Field(None, description="讯问人员警号 (逗号分隔)")


class InterrogationQAInput(BaseModel):
    """单个问答对 (用于 AI 建议输入和最终保存)"""
    q: str = Field(..., description="问题文本")
    a: str = Field(..., description="回答文本")

class InterrogationRecordCreate(BaseModel):
    """创建审讯记录的内部数据模型"""
    interrogator_id: int
    basic_info: Dict[str, Any]
    qas: List[Dict[str, str]]

class InterrogationRecordUpdate(BaseModel):
    """更新审讯记录的数据模型"""
    basic_info: Optional[Dict[str, Any]] = Field(None, description="更新后的基本信息 (可选)")
    qas: Optional[List[InterrogationQAInput]] = Field(None, description="完整的问答列表 (覆盖旧的)")
    status: Optional[str] = Field(None, description="状态 (e.g., 'ongoing', 'completed', 'cancelled')")
    full_text: Optional[str] = Field(None, description="最终生成的完整笔录文本 (可选)")

class InterrogationRecordRead(BaseModel):
    """读取或响应审讯记录的数据模型"""
    id: int
    interrogator_id: int
    basic_info: Optional[Dict[str, Any]] = Field(None, description="基础信息")
    qas: Optional[List[InterrogationQAInput]] = Field(None, description="问答对列表")
    status: str = Field(..., description="记录状态")
    full_text: Optional[str] = Field(None, description="完整笔录文本")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="最后更新时间")

    class Config:
        from_attributes = True

# [+] 新增: 用于列表展示的摘要模型
class InterrogationSummary(BaseModel):
    id: int
    person_name: Optional[str] = Field(None, description="被讯问人姓名")
    case_type: Optional[str] = Field(None, description="案件类型")
    status: str
    created_at: datetime
    updated_at: datetime
    interrogator_id: int

    # 从 basic_info 中提取 person_name 和 case_type
    @classmethod
    def from_orm(cls, obj: Any) -> 'InterrogationSummary':
        basic_info = obj.basic_info if isinstance(obj.basic_info, dict) else {}
        return cls(
            id=obj.id,
            person_name=basic_info.get("person_name"),
            case_type=basic_info.get("case_type"),
            status=obj.status,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
            interrogator_id=obj.interrogator_id
        )

# [+] 新增: 审讯记录列表的响应模型
class InterrogationListResponse(BaseModel):
    total: int = Field(..., description="记录总数")
    records: List[InterrogationSummary] = Field(..., description="当前页的审讯记录列表")