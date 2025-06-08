# FILE: alembic/env.py (修改后，启用 batch mode)
import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
# +++ 确保导入了 sqlalchemy +++
import sqlalchemy

from alembic import context

# +++ 添加这部分来设置路径和导入你的应用模块 +++
# 1. 计算项目根目录 (PROJECT_ROOT)
#    确保你的项目结构是 PsychologyAnalysis/alembic/env.py
try:
    # This assumes the env.py file is in PsychologyAnalysis/alembic/
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
except NameError: # Fallback if __file__ is not defined
    PROJECT_ROOT = os.path.abspath(os.path.join(os.getcwd(), '.'))
    print(f"警告: __file__ 未定义, 假设项目根目录是当前工作目录: {PROJECT_ROOT}")

# 2. 将项目根目录添加到 sys.path，这样 Python 就能找到 'app' 包
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
    print(f"[Alembic env.py] 已添加项目根目录到 sys.path: {PROJECT_ROOT}")
else:
    print(f"[Alembic env.py] 项目根目录已在 sys.path 中: {PROJECT_ROOT}")


# 3. 从你的应用导入 settings, Base, 和所有模型
try:
    # 导入配置
    from app.core.config import settings
    # 导入 SQLAlchemy Base
    from app.db.base_class import Base
    # +++ 显式导入所有需要被 Alembic 管理的模型 +++
    from app.models.user import User           # 导入 User 模型
    from app.models.assessment import Assessment # 导入 Assessment 模型
    from app.models.interrogation import InterrogationRecord # 导入审讯记录模型
    # 如果还有其他模型，也在这里导入:
    # from app.models.questionnaire import QuestionnaireQuestion # <--- 如果你决定保留并为其创建模型
    print("[Alembic env.py] 成功导入 settings, Base, 和模型 (User, Assessment, InterrogationRecord).") # 更新日志
except ImportError as e:
    print(f"[Alembic env.py] 导入应用模块时出错: {e}")
    print(f"请确认项目根目录 ({PROJECT_ROOT}) 是否正确，并且包含 'app' 包及其子模块 "
          f"(core.config, db.base_class, models.user, models.assessment, models.interrogation)。")
    sys.exit(1)
except Exception as e_import:
     print(f"[Alembic env.py] 在导入期间发生意外错误: {e_import}")
     sys.exit(1)
# --- 添加结束 ---


# 这是 Alembic 配置对象，提供对 .ini 文件值的访问
config = context.config

# 解析配置文件以进行 Python 日志记录。
# 这行代码基本上是设置日志记录器。
if config.config_file_name is not None:
    try:
        fileConfig(config.config_file_name)
        print(f"[Alembic env.py] 已从以下文件配置日志记录: {config.config_file_name}")
    except Exception as e_log:
        # 如果日志配置失败则避免崩溃，仅发出警告
        print(f"[Alembic env.py] 警告: 无法从 {config.config_file_name} 配置日志记录: {e_log}")


# 在这里添加你的模型的 MetaData 对象
# 以支持 'autogenerate'
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata

# +++ 设置 Alembic 需要知道的模型元数据 (现在包含了导入的所有模型) +++
print(f"[Alembic env.py] 从 {Base.__module__}.Base 设置 target_metadata")
target_metadata = Base.metadata
# --- 设置结束 ---

# +++ (可选) 调试代码，打印已注册的表名 +++
try:
    known_tables = list(target_metadata.tables.keys())
    print(f"[Alembic env.py] DEBUG: 在比较前，Base.metadata 中注册的表: {known_tables}")
except Exception as e_debug:
    print(f"[Alembic env.py] DEBUG: 获取元数据中的表名时出错: {e_debug}")
# +++ 调试代码结束 +++

# 从配置中获取的其他值，由 env.py 的需求定义，
# 可以这样获取:
# my_important_option = config.get_main_option("my_important_option")
# ... 等等。


def get_sync_database_url() -> str:
    """从设置中获取数据库 URL，并确保其对于 Alembic 是同步的。"""
    url = settings.DATABASE_URL
    # 将异步 sqlite 驱动替换为同步驱动
    if url and url.startswith("sqlite+aiosqlite"):
        sync_url = url.replace("sqlite+aiosqlite", "sqlite", 1)
        # print(f"[Alembic env.py] 为 Alembic 转换的数据库 URL: {sync_url}") # 减少冗余输出
        return sync_url
    # 如果需要，为其他异步驱动添加类似的替换
    # elif url and url.startswith("postgresql+asyncpg"):
    #     return url.replace("postgresql+asyncpg", "postgresql", 1)
    # print(f"[Alembic env.py] 为 Alembic 按原样使用数据库 URL: {url}") # 减少冗余输出
    return url # 如果未找到已知的异步驱动，则返回原始 URL


def run_migrations_offline() -> None:
    """在 'offline' 模式下运行迁移。"""
    sync_url = get_sync_database_url() # 获取可能修改过的同步 URL
    print(f"[Alembic env.py] 使用 URL 配置离线模式: {sync_url}")

    context.configure(
        url=sync_url,
        target_metadata=target_metadata,
        literal_binds=True, # 推荐用于脚本生成
        dialect_opts={"paramstyle": "named"},
        compare_type=True, # 启用类型比较
        compare_server_default=True, # 启用服务器默认值比较
        render_as_batch=True # <--- *** 在离线模式下也启用 Batch Mode ***
    )

    with context.begin_transaction():
        context.run_migrations()
    print("[Alembic env.py] 离线模式迁移完成。")


def run_migrations_online() -> None:
    """在 'online' 模式下运行迁移。"""
    # 获取同步 URL
    sync_url = get_sync_database_url()
    # 在 Alembic 配置对象中设置同步 URL，覆盖 alembic.ini
    config.set_main_option("sqlalchemy.url", sync_url)
    print(f"[Alembic env.py] 已将在线模式的 sqlalchemy.url 设置为: {sync_url}")

    try:
        # 使用配置中的同步 URL 创建引擎
        connectable = engine_from_config(
            config.get_section(config.config_ini_section, {}),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool, # 迁移时使用 NullPool
        )
        # print("[Alembic env.py] 在线模式的同步引擎创建成功。") # 减少冗余输出
    except Exception as e_engine:
         print(f"[Alembic env.py] 从配置创建同步引擎时出错: {e_engine}")
         sys.exit(1)

    # 使用同步引擎连接
    with connectable.connect() as connection:
        # print("[Alembic env.py] 在线模式的同步连接已建立。") # 减少冗余输出
        # 配置上下文，使用连接和元数据
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,            # 比较列类型
            compare_server_default=True,  # 比较服务器默认值
            # include_schemas=True, # 如果使用 PG schemas，取消注释
            render_as_batch=True # <--- *** 确保在线模式也启用 Batch Mode ***
        )
        # print("[Alembic env.py] 在线模式的上下文已配置。") # 减少冗余输出

        # 在事务中运行迁移
        try:
            print("[Alembic env.py] 开始事务并运行迁移...")
            with context.begin_transaction():
                context.run_migrations()
            print("[Alembic env.py] 迁移在事务中成功运行。")
        except Exception as e_migrate:
             print(f"[Alembic env.py] 运行迁移时出错: {e_migrate}")
             # 如果你希望命令明确失败，可以考虑重新抛出异常
             # raise e_migrate
        finally:
            # 连接会在 'with' 块结束时自动关闭
            pass


# --- 判断模式并运行 ---
if context.is_offline_mode():
    print("[Alembic env.py] 在离线模式下运行迁移。")
    run_migrations_offline()
else:
    print("[Alembic env.py] 在在线模式下运行迁移。")
    run_migrations_online()

print("[Alembic env.py] 脚本执行完毕。")