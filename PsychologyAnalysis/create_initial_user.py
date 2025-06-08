# create_initial_user.py
import sys
import os
import traceback
import logging
import asyncio # 导入 asyncio 用于运行异步代码
from getpass import getpass # 用于安全地获取密码输入

# --- 设置项目路径 (确保能找到 app 包) ---
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
# --------------------------------------------

# --- 导入必要的模块 ---
try:
    # 从 app.schemas 直接导入 UserCreate
    from app.schemas import UserCreate
    # 导入异步数据库组件
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.db.session import AsyncSessionLocal, async_engine
    # 导入异步 CRUD 函数
    from app.crud.user import get_user_by_username, create_user
    # 导入设置 (如果需要)
    from app.core.config import settings
    # 导入数据库 Base 和 User 模型
    from app.db.base_class import Base
    from app.models.user import User
except ImportError as e:
    print(f"导入应用模块时出错: {e}")
    print("请检查以下几点:")
    print("1. 您是否在 'PsychologyAnalysis' 目录下运行此脚本。")
    print("2. 必要的文件（如 app/db/session.py, app/crud/user.py, app/models/user.py, app/schemas/user.py）是否存在。")
    print("3. requirements.txt 中的所有依赖项是否已在您的环境中安装。")
    print("4. CRUD 函数 (get_user_by_username, create_user) 是否已定义为 'async def'。")
    print("5. app/schemas/__init__.py 是否正确导出了 UserCreate。")
    sys.exit(1)
except Exception as e:
     print(f"导入过程中发生意外错误: {e}")
     sys.exit(1)
# ------------------------

# --- 配置日志 ---
APP_LOGGER_NAME = settings.APP_NAME or "QingtingzheApp"
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(APP_LOGGER_NAME)
# ----------------

async def create_tables():
    """异步创建数据库表（如果尚不存在）"""
    logger.info("正在异步初始化数据库表...")
    try:
        async with async_engine.begin() as conn:
            # Base.metadata 包含了所有继承自 Base 的模型信息
            await conn.run_sync(Base.metadata.create_all)
        logger.info("数据库表已确认/创建成功。")
    except Exception as e:
        logger.error(f"创建数据库表时出错: {e}", exc_info=True)
        print(f"错误：无法创建数据库表。正在退出。错误: {e}")
        sys.exit(1)

async def create_user_interactively(db: AsyncSession) -> None:
    """交互式地获取用户信息并异步创建初始用户。"""
    logger.info("--- 正在创建初始用户 ---")

    while True:
        username = input("输入用户名: ").strip()
        if not username:
            print("用户名不能为空。")
            continue
        # 调用异步 CRUD 函数获取用户
        existing_user = await get_user_by_username(db, username=username)
        if existing_user:
            print(f"用户名 '{username}' 已存在。请选择其他用户名。")
        else:
            break

    email_str = input(f"为 {username} 输入邮箱 (可选, 直接按 Enter 跳过): ").strip()
    email = email_str if email_str else None
    full_name = input(f"为 {username} 输入全名 (可选, 直接按 Enter 跳过): ").strip() or None

    while True:
        password = getpass("输入密码 (最少6位): ")
        if len(password) < 6:
            print("密码太短 (最少6位)。")
            continue
        password_confirm = getpass("确认密码: ")
        if password != password_confirm:
            print("两次输入的密码不匹配，请重试。")
        else:
            break

    is_superuser_input = input("是否将此用户设为超级用户? (y/N): ").strip().lower()
    is_superuser = True if is_superuser_input == 'y' else False

    # 使用 Pydantic schema 准备用户数据
    user_in = UserCreate( # <-- 直接使用导入的 UserCreate
        username=username,
        email=email,
        full_name=full_name,
        password=password, # 传递明文密码，哈希在 crud.create_user 中完成
        is_superuser=is_superuser,
        is_active=True # 初始用户通常是激活的
    )

    try:
        logger.info(f"尝试创建用户: {user_in.username} (超级用户: {is_superuser})")
        # --- 关键修改：使用正确的关键字参数名 ---
        # created_user = await create_user(db=db, user=user_in) # 旧的，错误的调用
        created_user = await create_user(db=db, user_in=user_in) # <--- 使用 'user_in='
        # -----------------------------------------
        logger.info(f"成功创建用户: '{created_user.username}' (ID: {created_user.id})")
        print(f"\n用户 '{created_user.username}' 创建成功!")
    except ValueError as ve: # 捕获来自 CRUD 的特定错误 (如重复用户)
         logger.error(f"创建用户 '{username}' 失败: {ve}")
         print(f"\n错误：无法创建用户。{ve}")
    except Exception as e:
        logger.error(f"创建用户 '{username}' 时发生意外错误: {e}", exc_info=True)
        print(f"\n错误：发生意外错误: {e}")


async def main():
    """主异步执行函数"""
    await create_tables() # 先确保表存在

    logger.info("正在创建数据库会话...")
    # 正确使用异步会话上下文管理器
    async with AsyncSessionLocal() as session:
        await create_user_interactively(session)

    logger.info("脚本执行完毕。")


if __name__ == "__main__":
    print("开始执行用户创建脚本...")
    try:
        # 运行主异步函数
        asyncio.run(main())
    except KeyboardInterrupt:
         print("\n用户中断了脚本执行。")
    except Exception as e:
         print(f"\n在顶层发生意外错误: {e}")
         traceback.print_exc() # 打印完整的错误堆栈