# FILE: app/crud/__init__.py (更新后)
from . import user          # 用户相关 CRUD
from . import assessment    # 评估相关 CRUD
from . import interrogation # 审讯记录相关 CRUD
from . import stats         # 统计相关 CRUD
from . import attribute     # +++ 属性相关 CRUD +++

# (可选) 可以在这里定义 __all__
__all__ = [
    "user",
    "assessment",
    "interrogation",
    "stats",
    "attribute", # <--- 添加 attribute
]