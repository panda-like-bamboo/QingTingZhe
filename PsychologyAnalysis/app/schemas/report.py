# FILE: app/schemas/report.py (修改后，添加 attributes 字段)
from pydantic import BaseModel, Field # 确保 Field 已导入
from typing import Optional, Dict, Any, List # <--- 导入 List
from datetime import datetime

# +++ 新增：定义用于在报告中展示的属性信息 Schema +++
# （理想情况下，这个模型应该在 app/schemas/attribute.py 中定义并从那里导入）
class AttributeRead(BaseModel):
    id: int
    name: str = Field(..., description="属性名称，例如'焦虑'、'高风险'")
    # 可以选择性地包含 description 或 category
    # description: Optional[str] = None
    # category: Optional[str] = None

    class Config:
        from_attributes = True # 允许从 ORM 对象属性创建
# +++ 属性 Schema 定义结束 +++


class ReportData(BaseModel):
    """报告详情的响应模型 (包含关联属性)"""
    id: int
    image_path: Optional[str] = None
    subject_name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    questionnaire_type: Optional[str] = None
    questionnaire_data: Optional[Dict[str, Any]] = None # 解析后的 JSON
    report_text: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    id_card: Optional[str] = None
    occupation: Optional[str] = None
    case_name: Optional[str] = None
    case_type: Optional[str] = None
    identity_type: Optional[str] = None
    person_type: Optional[str] = None
    marital_status: Optional[str] = None
    children_info: Optional[str] = None
    criminal_record: Optional[int] = None
    health_status: Optional[str] = None
    phone_number: Optional[str] = None
    domicile: Optional[str] = None
    status: Optional[str] = None # 报告状态

    # +++ 新增：关联的属性列表 +++
    # 这个字段将包含与此评估关联的所有属性对象的信息
    # 默认值为 None 或空列表 [] 都可以，取决于你的偏好
    attributes: Optional[List[AttributeRead]] = Field(default_factory=list, description="与此评估关联的属性标签列表")
    # +++ 属性字段添加结束 +++

    class Config: # Pydantic V2 使用 ConfigDict 或直接设置
        from_attributes = True # 保持不变，以便从 Assessment ORM 对象加载数据
    # ... 可以添加未来需要的其他报告字段 ...

class ReportResponse(BaseModel):
    """获取报告的 API 响应"""
    report: Optional[ReportData] = None
    message: Optional[str] = None # 用于传递状态信息（如处理中）或错误
    # error 字段可以移除，统一使用 message 字段

# 状态响应模型保持不变
class ReportStatusResponse(BaseModel):
    status: str