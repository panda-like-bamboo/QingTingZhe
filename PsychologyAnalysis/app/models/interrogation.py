# FILE: app/models/interrogation.py (新建)
from sqlalchemy import Column, Integer, String, JSON, TIMESTAMP, ForeignKey, Text
from sqlalchemy.sql import func
from app.db.base_class import Base

class InterrogationRecord(Base):
    __tablename__ = "interrogation_records"

    id = Column(Integer, primary_key=True, index=True)
    # 关联进行审讯的管理员 (假设 User 模型已存在)
    interrogator_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    # 存储 JSON 格式的基础信息
    basic_info = Column(JSON, nullable=True)
    # 存储 JSON 格式的问答对列表 [{'q': '...', 'a': '...'}, ...]
    qas = Column(JSON, nullable=True)
    # 记录状态: ongoing, completed, cancelled
    status = Column(String(50), nullable=False, default="ongoing", index=True)
    # 完整的审讯文本 (可选，如果需要存储最终格式化文本)
    full_text = Column(Text, nullable=True)

    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        person_name = self.basic_info.get("person_name", "未知") if isinstance(self.basic_info, dict) else "未知"
        return f"<InterrogationRecord(id={self.id}, person='{person_name}', status='{self.status}')>"

# --- 如果使用 SQLite，可能需要为 JSON 列添加索引（取决于具体查询需求） ---
# from sqlalchemy import Index
# Index('ix_interrogation_basic_info_name', InterrogationRecord.basic_info['person_name']) # 示例