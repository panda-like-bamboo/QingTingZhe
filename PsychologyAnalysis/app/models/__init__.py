from .user import User
from .assessment import Assessment
from .interrogation import InterrogationRecord
from .attribute import Attribute # <--- 新增导入
# 关联表通常不需要在这里导出，除非你直接使用它

__all__ = [
    "User",
    "Assessment",
    "InterrogationRecord",
    "Attribute", # <--- 添加到列表
]