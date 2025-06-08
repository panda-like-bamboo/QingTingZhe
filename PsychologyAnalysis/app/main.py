# 文件路径: PsychologyAnalysis/app/main.py

# 文件路径: PsychologyAnalysis/app/main.py (最终修复版)

import sys
import os
import logging
import traceback
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response

# --- 1. 路径设置 ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# --- 2. 核心导入 ---
try:
    from app.core.config import settings, parsed_cors_origins
    from src.utils import setup_logging
except ImportError as e:
    print(f"[启动错误] 无法导入核心配置或日志设置: {e}")
    traceback.print_exc()
    sys.exit(1)

# --- 3. 日志配置 ---
APP_LOGGER_NAME = settings.APP_NAME or "PsychologyAnalysisApp"
try:
    log_dir = settings.LOGS_DIR
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    setup_logging(
        log_level_str=settings.LOG_LEVEL,
        log_dir_name=os.path.basename(log_dir),
        log_dir_base_path=os.path.dirname(log_dir),
        logger_name=APP_LOGGER_NAME
    )
    logger = logging.getLogger(APP_LOGGER_NAME)
    logger.info("=" * 50)
    logger.info("--- 启动 FastAPI 应用 ---")
except Exception as e:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(APP_LOGGER_NAME)
    logger.critical(f"[启动错误] 日志系统设置失败: {e}。", exc_info=True)

# --- 4. 路由导入 ---
try:
    from app.routers import scales, assessments, reports, auth, encyclopedia, sse, admin
    logger.info("所有API路由模块导入成功。")
except ImportError as e:
    logger.critical(f"[启动错误] 无法导入路由模块: {e}", exc_info=True)
    sys.exit(1)

# --- 5. FastAPI 应用实例 ---
app = FastAPI(
    title=settings.APP_NAME,
    description="倾听者AI智能警务分析评估应用系统 API",
    version="1.0.1", # 版本号提升
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)
logger.info(f"FastAPI应用 '{settings.APP_NAME}' 实例已创建。")

# --- 6. CORS 中间件 ---
if parsed_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=parsed_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info(f"CORS中间件已启用，允许的来源: {parsed_cors_origins}")

# --- 7. API 路由注册 ---
logger.info("开始注册API路由...")
app.include_router(auth.router, prefix=settings.API_V1_STR, tags=["认证 (Auth)"])
app.include_router(scales.router, prefix=settings.API_V1_STR, tags=["量表 (Scales)"])
app.include_router(assessments.router, prefix=settings.API_V1_STR, tags=["评估 (Assessments)"])
# 注意：reports.py 中的路径现在是相对于 /api/v1/reports
app.include_router(reports.router, prefix=f"{settings.API_V1_STR}/reports", tags=["报告 (Reports)"])
app.include_router(encyclopedia.router, prefix=settings.API_V1_STR, tags=["心理百科 (Encyclopedia)"])
# admin.py 中的路径现在是相对于 /api/v1/admin
app.include_router(admin.router, prefix=f"{settings.API_V1_STR}/admin", tags=["后台管理 (Admin)"])
app.include_router(sse.router, tags=["SSE 事件流"])
logger.info("所有API路由注册完成。")


# --- 8. 静态文件服务和 SPA 回退路由 ---
ADMIN_FRONTEND_DIR = os.path.join(PROJECT_ROOT, "psychology-admin-frontend", "dist-admin")

if os.path.isdir(ADMIN_FRONTEND_DIR):
    logger.info(f"找到后台管理前端构建目录: {ADMIN_FRONTEND_DIR}")

    # 将 /admin 路径下的请求映射到 dist-admin 目录，并让 index.html 成为默认文件
    app.mount("/admin", StaticFiles(directory=ADMIN_FRONTEND_DIR, html=True), name="admin_app")
    logger.info(f"URL路径 '/admin' 已成功挂载到静态文件目录: {ADMIN_FRONTEND_DIR}")

    @app.middleware("http")
    async def spa_fallback(request: Request, call_next):
        """
        中间件，用于处理所有指向前端单页应用（SPA）的深层链接。
        """
        response = await call_next(request)
        # 检查是否是针对后台 /admin/ 的请求，并且返回了404
        if response.status_code == 404 and request.url.path.startswith('/admin/'):
            index_path = os.path.join(ADMIN_FRONTEND_DIR, "index.html")
            if os.path.exists(index_path):
                logger.debug(f"SPA回退: 为路径 {request.url.path} 提供 index.html")
                return FileResponse(index_path)
        return response

else:
    logger.warning(f"后台管理前端目录未找到: {ADMIN_FRONTEND_DIR}。请运行 'npm run build'。")
# --- 9. 欢迎根路径 ---
@app.get("/", tags=["Root"])
async def read_root():
    """根路径，返回欢迎信息。"""
    return {"message": f"欢迎使用 {settings.APP_NAME}", "version": app.version}


# --- 10. 最终启动信息 ---
logger.info("=" * 50)
logger.info(f"FastAPI 应用 '{settings.APP_NAME}' 已完成配置并准备就绪。")
logger.info(f"当前环境: {settings.ENVIRONMENT}")
logger.info("服务已启动，等待接收请求...")
logger.info("=" * 50)


# --- 11. Uvicorn 开发服务器运行器 ---
# 此部分仅在直接运行 `python app/main.py` 时执行
if __name__ == "__main__":
    import uvicorn
    logger.info("检测到直接运行 main.py，将启动 Uvicorn 开发服务器...")
    
    # 从配置中获取 host 和 port
    run_host = getattr(settings, 'HOST', '0.0.0.0') # 默认 0.0.0.0
    try:
        run_port = int(os.environ.get('PORT', '8000'))
    except ValueError:
        run_port = 8000
        logger.warning(f"无效的PORT环境变量，使用默认端口 {run_port}。")

    # 仅在开发环境启用代码自动重载
    reload_flag = settings.ENVIRONMENT == "development"
    
    log_config_level = settings.LOG_LEVEL.lower()
    logger.info(f"服务器将在 http://{run_host}:{run_port} 上运行")
    logger.info(f"代码自动重载: {'启用' if reload_flag else '禁用'}")
    logger.info(f"Uvicorn 日志级别: {log_config_level}")

    try:
        uvicorn.run(
            "app.main:app",
            host=run_host,
            port=run_port,
            reload=reload_flag,
            log_level=log_config_level,
        )
    except Exception as e:
        logger.critical(f"[启动错误] 启动 Uvicorn 服务器失败: {e}", exc_info=True)
        sys.exit(1)