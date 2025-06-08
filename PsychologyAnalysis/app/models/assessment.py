# FILE: app/models/assessment.py (修改后，添加与 Attribute 的多对多关系)
from sqlalchemy import ( # 按字母顺序或分组导入，更清晰
    Table, # <--- 新增: 用于定义关联表
    Column,
    Integer,
    String,
    Boolean,
    Text,
    TIMESTAMP,
    ForeignKey,
    Index
)
from sqlalchemy.orm import relationship # <--- 新增: 用于定义 ORM 关系
from sqlalchemy.sql import func
from .association_tables import assessment_attributes_table
from app.db.base_class import Base # 确保从正确的路径导入 Base
# 注意: Attribute 模型将在 app/models/attribute.py 中定义

# --- 关联表定义 (多对多: Assessment <-> Attribute) ---
# 这个表不需要自己的模型类，SQLAlchemy 会通过 relationship 处理它
# assessment_attributes_table = Table(
#     "assessment_attributes", # 数据库中的关联表名
#     Base.metadata, # 关联到 Base 的元数据
#     Column("assessment_id", Integer, ForeignKey("analysis_data.id"), primary_key=True), # 外键指向 Assessment 表，是复合主键的一部分
#     Column("attribute_id", Integer, ForeignKey("attributes.id"), primary_key=True)   # 外键指向 Attribute 表，是复合主键的一部分
#     # 注意: ForeignKey("attributes.id") 假设你将在 attribute.py 中创建名为 "attributes" 的表
# )
# --- 关联表定义结束 ---

# 定义状态常量 (可选，但推荐)
STATUS_PENDING = "pending"
STATUS_PROCESSING = "processing"
STATUS_COMPLETE = "complete"
STATUS_FAILED = "failed"

class Assessment(Base):
    __tablename__ = "analysis_data" # 数据库中的表名

    id = Column(Integer, primary_key=True, index=True) # 主键，自动索引
    image_path = Column(Text, nullable=True) # 图片文件相对路径或标识符
    subject_name = Column(String(200), index=True) # 被测者姓名，添加索引便于查询
    age = Column(Integer) # 年龄
    gender = Column(String(10)) # 性别
    questionnaire_type = Column(String(100), nullable=True) # 使用的量表类型代码
    questionnaire_data = Column(Text, nullable=True) # 存储量表答案的 JSON 字符串
    report_text = Column(Text, nullable=True) # 存储生成的报告文本

    # 时间戳
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False) # 创建时间，数据库自动设置
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False) # 更新时间

    # 详细信息字段
    id_card = Column(String(50), unique=True, index=True, nullable=True) # 身份证号，唯一且有索引
    occupation = Column(String(100), nullable=True) # 职业
    case_name = Column(String(200), nullable=True) # 案件名称
    case_type = Column(String(100), nullable=True) # 案件类型
    identity_type = Column(String(100), nullable=True) # 人员身份
    person_type = Column(String(100), nullable=True) # 人员类型
    marital_status = Column(String(50), nullable=True) # 婚姻状况
    children_info = Column(Text, nullable=True) # 子女情况 (文本描述)
    criminal_record = Column(Integer, default=0, nullable=False) # 有无犯罪前科 (0:无, 1:有)
    health_status = Column(Text, nullable=True) # 健康情况 (文本描述)
    phone_number = Column(String(50), nullable=True) # 手机号
    domicile = Column(String(200), nullable=True) # 归属地

    # 外键，链接到提交此评估的用户
    submitter_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True) # 提交者用户ID，允许为空，添加索引

    # 评估状态字段
    status = Column(
        String(30),
        nullable=False,
        default=STATUS_PENDING,
        server_default=STATUS_PENDING,
        index=True
    )

    # --- 新增的多对多关系 ---
    # 定义与 Attribute 模型的关系
    # secondary=assessment_attributes_table 指定了用于连接的关联表
    # back_populates="assessments" 用于在 Attribute 模型中建立反向关系，
    #   假设 Attribute 模型中会有一个名为 'assessments' 的关系指向 Assessment
    # lazy="selectin" 是一种推荐的加载策略，可以在访问 assessment.attributes 时高效加载关联的属性
    attributes = relationship(
        "Attribute", # 指向关联的模型类名 (字符串形式，避免循环导入)
        secondary=assessment_attributes_table, # 指定关联表
        back_populates="assessments", # 指定对方模型中的反向关系属性名
        lazy="selectin" # 推荐的加载策略
    )
    # --- 关系定义结束 ---

    # --- (可选) 与 User 的关系 ---
    # 如果 User 模型中定义了 back_populates="assessments"
    # submitter = relationship("User", back_populates="assessments", lazy="selectin")
    # --- 关系定义结束 ---

    # (可选) 定义表级索引，如果需要复合索引
    # __table_args__ = (
    #     Index('ix_assessment_id_card_status', 'id_card', 'status'), # 示例复合索引
    # )

    def __repr__(self):
        """提供一个方便调试的对象表示"""
        return (f"<Assessment(id={self.id}, subject='{self.subject_name}', "
                f"type='{self.questionnaire_type}', status='{self.status}')>")