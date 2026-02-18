"""
邮箱账户模型
"""
from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.email import Email
    from app.models.folder import Folder


class ProviderType(str, PyEnum):
    """邮箱提供商类型"""
    MICROSOFT = "microsoft"      # Microsoft 365 / Outlook
    GOOGLE = "google"            # Gmail
    IMAP = "imap"                # 通用 IMAP


class AuthType(str, PyEnum):
    """认证方式"""
    PASSWORD = "password"        # 普通密码 / 应用专用密码
    OAUTH2 = "oauth2"            # OAuth2 (Access Token / Refresh Token)


class AccountStatus(str, PyEnum):
    """账户状态"""
    ACTIVE = "active"            # 正常
    ERROR = "error"              # 错误
    SYNCING = "syncing"          # 同步中
    DISABLED = "disabled"        # 已禁用
    AUTH_REQUIRED = "auth_required"  # 需要重新授权


class EmailAccount(Base):
    """邮箱账户模型"""
    
    __tablename__ = "email_accounts"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # 外键关联
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    
    # 账户基本信息
    email_address: Mapped[str] = mapped_column(
        String(255), index=True, nullable=False
    )
    display_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # 提供商类型
    provider: Mapped[ProviderType] = mapped_column(
        Enum(ProviderType), nullable=False
    )
    
    # 认证方式
    auth_type: Mapped[AuthType] = mapped_column(
        Enum(AuthType), default=AuthType.PASSWORD
    )
    
    # 账户状态
    status: Mapped[AccountStatus] = mapped_column(
        Enum(AccountStatus), default=AccountStatus.ACTIVE
    )
    status_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # OAuth 凭证 (支持自定义 Client ID)
    client_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    client_secret: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    access_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    refresh_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    token_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # IMAP 配置
    imap_server: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    imap_port: Mapped[Optional[int]] = mapped_column(Integer, default=993)
    imap_use_ssl: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # 密码认证信息 (如果是 OAuth，此字段为空)
    imap_username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True) # 登录名
    imap_password: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # 加密存储
    
    # 同步配置
    sync_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    sync_folder: Mapped[str] = mapped_column(String(255), default="INBOX")
    
    # 统计信息
    total_emails: Mapped[int] = mapped_column(Integer, default=0)
    unread_count: Mapped[int] = mapped_column(Integer, default=0)
    storage_used: Mapped[int] = mapped_column(Integer, default=0)  # 字节
    
    # 代理设置 (可选，覆盖全局)
    proxy_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    
    # 关联关系
    user: Mapped["User"] = relationship("User", back_populates="email_accounts")
    emails: Mapped[list["Email"]] = relationship(
        "Email",
        back_populates="account",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    folders: Mapped[list["Folder"]] = relationship(
        "Folder",
        back_populates="account",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        return f"<EmailAccount(id={self.id}, email={self.email_address}, provider={self.provider})>"
    
    def to_dict(self, include_credentials: bool = False) -> dict:
        """转换为字典"""
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "email_address": self.email_address,
            "display_name": self.display_name,
            "provider": self.provider.value,
            "auth_type": self.auth_type.value,
            "status": self.status.value,
            "status_message": self.status_message,
            "sync_enabled": self.sync_enabled,
            "last_sync_at": self.last_sync_at.isoformat() if self.last_sync_at else None,
            "sync_folder": self.sync_folder,
            "total_emails": self.total_emails,
            "unread_count": self.unread_count,
            "storage_used": self.storage_used,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "proxy_url": self.proxy_url,
        }
        
        if include_credentials:
            data.update({
                "client_id": self.client_id,
                "client_secret": self.client_secret,  # 完整备份需要
                "refresh_token": self.refresh_token,
                "access_token": self.access_token,  # 添加 access_token
                "token_expires_at": self.token_expires_at.isoformat() if self.token_expires_at else None,
                "imap_server": self.imap_server,
                "imap_port": self.imap_port,
                "imap_use_ssl": self.imap_use_ssl,
                "imap_username": self.imap_username,
                "imap_password": self.imap_password,  # 关键：密码
            })
        
        return data
