#!/usr/bin/env python3
"""
Mailbox Manager - 后端服务入口

一个现代化的多邮箱管理工具，支持 Microsoft 365、Gmail 和 IMAP 协议。
"""
import asyncio
import logging
import sys
import os
from contextlib import asynccontextmanager
from datetime import datetime

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 导入配置和核心模块
try:
    from app.core.config import settings
    from app.core.database import init_db, close_db, check_db_connection
    from app.core.exceptions import BaseAPIException
    logger.info("核心模块加载成功")
except Exception as e:
    logger.error(f"核心模块加载失败: {e}")
    raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("🚀 启动 Mailbox Manager 后端服务...")
    
    # 初始化数据库
    try:
        logger.info("📦 初始化数据库...")
        await init_db()
        
        # 检查数据库连接
        if await check_db_connection():
            logger.info("✅ 数据库连接正常")
        else:
            logger.warning("⚠️ 数据库连接异常")
            
    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {e}")
        raise
    
    logger.info(f"✨ {settings.app_name} v{settings.app_version} 启动成功!")
    logger.info(f"📍 环境: {'开发' if settings.debug else '生产'}")
    
    yield  # 应用运行期间
    
    # 关闭时清理
    logger.info("🛑 正在关闭服务...")
    await close_db()
    logger.info("👋 服务已关闭")


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    现代化的多邮箱管理工具 API，支持 Microsoft 365、Gmail 和 IMAP 协议。
    """,
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json",
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else ["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由
def register_routers():
    """注册所有 API 路由"""
    try:
        from app.api.v1 import api_v1
        app.include_router(api_v1, prefix="/api/v1")
        logger.info("✅ API v1 路由注册成功")
    except Exception as e:
        logger.error(f"❌ API 路由注册失败: {e}")
        raise

# 在启动时注册路由
register_routers()


# 异常处理
@app.exception_handler(BaseAPIException)
async def api_exception_handler(request, exc: BaseAPIException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.status_code,
                "message": exc.detail
            }
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    logger.exception(f"未处理的异常: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": 500,
                "message": "服务器内部错误"
            }
        }
    )

@app.get("/health", tags=["系统"], summary="健康检查")
async def health_check():
    db_status = await check_db_connection()
    return {
        "success": True,
        "data": {
            "status": "healthy" if db_status else "degraded",
            "version": settings.app_version,
            "database": "connected" if db_status else "disconnected",
            "timestamp": datetime.utcnow().isoformat()
        }
    }

@app.get("/api-info", tags=["系统"], summary="服务信息")
async def root():
    return {
        "success": True,
        "data": {
            "name": settings.app_name,
            "version": settings.app_version,
            "description": "现代化的多邮箱管理工具",
            "docs": "/docs" if settings.debug else None,
            "health": "/health"
        }
    }

# --- 关键修改: 静态文件服务 (用于 EXE 打包 / 生产环境) ---
# 1. 尝试找到 frontend/dist 目录 (开发环境 ../frontend/dist, 打包后 ./dist)
dist_dir = os.path.join(os.path.dirname(__file__), "dist")
if not os.path.exists(dist_dir):
    # 尝试上级目录 (开发模式)
    dist_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")

if os.path.exists(dist_dir) and os.path.exists(os.path.join(dist_dir, "index.html")):
    logger.info(f"📁 挂载前端静态资源: {dist_dir}")
    
    # 挂载 assets 目录 (JS/CSS/Images)
    if os.path.exists(os.path.join(dist_dir, "assets")):
        app.mount("/assets", StaticFiles(directory=os.path.join(dist_dir, "assets")), name="assets")

    # 挂载 favicon.ico
    @app.get("/favicon.ico", include_in_schema=False)
    async def favicon():
        return FileResponse(os.path.join(dist_dir, "favicon.ico"))

    # 所有未匹配 API 的请求都返回 index.html (SPA 支持)
    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        # 排除 API 路径
        if full_path.startswith("api") or full_path.startswith("docs") or full_path.startswith("redoc"):
            raise HTTPException(status_code=404, detail="Not Found")
            
        # 尝试直接返回文件 (如果存在且不是目录)
        file_path = os.path.join(dist_dir, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
            
        # 默认返回 index.html
        return FileResponse(os.path.join(dist_dir, "index.html"))
else:
    logger.warning(f"⚠️ 前端构建产物未找到，仅提供 API 服务。路径: {dist_dir}")


if __name__ == "__main__":
    # 开发模式启动
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    )
