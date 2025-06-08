# FILE: app/models/association_tables.py
from sqlalchemy import Table, Column, Integer, ForeignKey
from app.db.base_class import Base # 导入 Base 以获取 metadata

# 定义评估与属性的关联表
assessment_attributes_table = Table(
    "assessment_attributes", # 表名
    Base.metadata,           # 关联到 Base 的元数据
    Column("assessment_id", Integer, ForeignKey("analysis_data.id"), primary_key=True), # 外键关联 analysis_data 表的 id
    Column("attribute_id", Integer, ForeignKey("attributes.id"), primary_key=True)     # 外键关联 attributes 表的 id
)