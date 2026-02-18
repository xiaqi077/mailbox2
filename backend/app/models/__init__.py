"""
数据模型模块
"""
from app.models.user import User
from app.models.email_account import EmailAccount
from app.models.email import Email
from app.models.folder import Folder

__all__ = ["User", "EmailAccount", "Email", "Folder"]