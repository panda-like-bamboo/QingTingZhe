# conda
conda activate listener

# 依赖
pip install -r requirements.txt 来安装所有依赖
pip install --force-reinstall -r requirements.txt。这会确保即使包已存在，也会尝试重新安装，有时能解决损坏的安装。

# 进度
核心的 FastAPI 框架、API 端点（用于量表、提交、报告获取）以及 Celery 异步 AI 处理流程都已经成功搭建并初步验证

# 进程1
在执行前，打开redis windows为：redis-server.exe

python run_celery_worker.py #运行该代码来 启动celery worker(这个就行)
celery -A app.core.celery_app worker --loglevel=info -P solo # Windows 使用 solo 进程池

# 进程2

uvicorn app.main:app --reload
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 --log-level info 启动 FastAPI 服务器 (Uvicorn)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --log-level info 启动 FastAPI 服务器 (Uvicorn)  -->全局广播，用于局域网，记得关闭防火墙 -->ip：http://192.168.43.190:5173/（我手机热点）


# 记得打开前端
npm run dev

# 手动创建用户 尤其是管理员的
python create_initial_user.py

# 进程0:
## 数据库初始化
从终端运行 python -m app.db.init_db。这会连接到 config.py 中 DATABASE_URL 指定的 SQLite 文件，并创建 users 表（如果它还不存在）。

## 数据库迁移 使用 Alembic
安装 Alembic: pip install alembic
初始化 Alembic: 在项目根目录运行 alembic init alembic (会创建一个 alembic 文件夹和 alembic.ini 文件)。
配置 Alembic: 修改 alembic/env.py 文件，让它能连接到你的数据库并识别你的 SQLAlchemy Base。你需要：
导入你的 Base: from app.db.base_class import Base
设置 target_metadata = Base.metadata
配置数据库 URL (可以从 settings 导入)。
自动生成迁移脚本: 运行 alembic revision --autogenerate -m "Add submitter_id to analysis_data"。Alembic 会比较你的模型和数据库，并在 alembic/versions/ 目录下生成一个 Python 文件，包含添加 submitter_id 列的 SQL 操作。
检查迁移脚本: 打开生成的脚本文件，确认它包含了类似 op.add_column('analysis_data', sa.Column('submitter_id', sa.Integer(), nullable=True)) 和 op.create_foreign_key(...)、op.create_index(...) 的操作。
应用迁移: 运行 *alembic upgrade head* 这会执行迁移脚本，更新你的数据库表结构。

## 量表导入：
导入input\questionnaires里面的量表
python src/import_questions.py

使用总结：
1.
alembic revision --autogenerate -m "Create users table and add submitter_id fk"
2.
alembic upgrade head


# 运行应用: 确保你的 FastAPI 应用和 Celery worker 都在运行。（两个进程：1 2）
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
python run_celery_worker.py (或 celery -A ...)

# 注意！！！！

1. pages.py
下面内容注销了，所以这里没有依赖，等有机会再修复。先能跑

     添加依赖项，确保只有激活的用户才能访问此页面
     dependencies=[Depends(get_current_active_user)]