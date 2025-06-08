from sqlalchemy import Column, Integer, String, Boolean
from app.db.base_class import Base # 从我们创建的基类导入

class User(Base):
    __tablename__ = "users" # 数据库中的表名

    id = Column(Integer, primary_key=True, index=True)
    # 用户名，唯一且加索引，不允许为空
    username = Column(String(100), unique=True, index=True, nullable=False)
    # 邮箱，唯一且加索引，可以为空
    email = Column(String(255), unique=True, index=True, nullable=True)
    # 存储哈希后的密码，不允许为空
    hashed_password = Column(String(255), nullable=False)
    # 全名，可以为空
    full_name = Column(String(100), nullable=True)
    # 是否激活，默认为 True
    is_active = Column(Boolean(), default=True, nullable=False)
    # 是否为超级管理员，默认为 False
    is_superuser = Column(Boolean(), default=False, nullable=False)

    # __repr__ 方法用于方便调试时打印对象信息
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"

# 你可以在这里定义其他模型，如 Assessment, Report 等
# 它们都需要继承自 Base