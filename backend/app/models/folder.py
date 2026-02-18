"""
邮箱文件夹模型
"""
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.email_account import EmailAccount
    from app.models.email import Email


class Folder(Base):
    """邮箱文件夹模型"""
    
    __tablename__ = "folders"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # 外键关联
    account_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("email_accounts.id", ondelete="CASCADE"), nullable=False
    )
    
    # 文件夹信息
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    path: Mapped[str] = mapped_column(String(500), nullable=False)  # 完整路径
    
    # 特殊文件夹标记
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    folder_type: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # inbox, sent, drafts, trash, spam, etc.
    
    # 统计信息
    total_count: Mapped[int] = mapped_column(Integer, default=0)
    unread_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # 同步状态
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    uidvalidity: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    
    # 关联关系
    account: Mapped["EmailAccount"] = relationship("EmailAccount", back_populates="folders")
    emails: Mapped[list["Email"]] = relationship(
        "Email",
        back_populates="folder",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        return f"<Folder(id={self.id}, name={self.name}, path={self.path})>"
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "account_id": self.account_id,
            "name": self.name,
            "path": self.path,
            "is_system": self.is_system,
            "folder_type": self.folder_type,
            "total_count": self.total_count,
            "unread_count": self.unread_count,
            "last_sync_at": self.last_sync_at.isoformat() if self.last_sync_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }