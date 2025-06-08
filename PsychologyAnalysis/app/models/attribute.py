# FILE: app/models/attribute.py
from sqlalchemy import Column, Integer, String, Text, Index
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from .association_tables import assessment_attributes_table # 稍后创建这个文件

class Attribute(Base):
    __tablename__ = "attributes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False) # 属性名称，唯一且索引
    description = Column(Text, nullable=True)                          # 属性描述
    category = Column(String(50), index=True, nullable=True)           # 属性分类（可选）

    # 定义与 Assessment 的多对多关系
    # 'assessments' 是在 Attribute 实例上访问关联 Assessment 对象的属性名
    # secondary 指向我们即将定义的关联表
    # back_populates 用于双向关系，需要在 Assessment 模型中定义 'attributes'
    assessments = relationship(
        "Assessment",
        secondary=assessment_attributes_table,
        back_populates="attributes" # 与 Assessment 模型中的关系名对应
    )

    def __repr__(self):
        return f"<Attribute(id={self.id}, name='{self.name}', category='{self.category}')>"

# 可以添加表级索引
# __table_args__ = (
#     Index('ix_attribute_category_name', 'category', 'name'),
# )