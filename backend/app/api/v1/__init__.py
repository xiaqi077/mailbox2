"""
API v1 路由
"""
from fastapi import APIRouter

from app.api.v1 import auth, users, accounts, emails, folders, websocket, settings

api_v1 = APIRouter()

# 注册各模块路由
api_v1.include_router(auth.router, prefix="/auth", tags=["认证"])
api_v1.include_router(users.router, prefix="/users", tags=["用户"])
api_v1.include_router(accounts.router, prefix="/accounts", tags=["邮箱账户"])
api_v1.include_router(folders.router, prefix="/folders", tags=["文件夹"])
api_v1.include_router(emails.router, prefix="/emails", tags=["邮件"])
api_v1.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])
api_v1.include_router(settings.router, prefix="/settings", tags=["系统设置"])