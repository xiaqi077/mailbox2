"""
邮件模型
"""
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Text, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.email_account import EmailAccount
    from app.models.folder import Folder


class Email(Base):
    """邮件模型"""
    
    __tablename__ = "emails"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # 外键关联
    account_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("email_accounts.id", ondelete="CASCADE"), nullable=False
    )
    folder_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("folders.id", ondelete="CASCADE"), nullable=False
    )
    
    # 邮件标识
    uid: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    message_id: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, index=True)
    thread_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    
    # 邮件头信息
    subject: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    from_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    from_address: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    to_addresses: Mapped[str] = mapped_column(Text, nullable=False)
    cc_addresses: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    bcc_addresses: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reply_to: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # 邮件内容
    body_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    body_html: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # 邮件状态
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_flagged: Mapped[bool] = mapped_column(Boolean, default=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # 邮件属性
    has_attachments: Mapped[bool] = mapped_column(Boolean, default=False)
    attachments_count: Mapped[int] = mapped_column(Integer, default=0)
    size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # 时间戳
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    received_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    
    # 关联关系
    account: Mapped["EmailAccount"] = relationship("EmailAccount", back_populates="emails")
    folder: Mapped["Folder"] = relationship("Folder", back_populates="emails")
    
    def __repr__(self) -> str:
        return f"<Email(id={self.id}, subject={self.subject[:30] if self.subject else None}, from={self.from_address})>"
    
    def to_dict(self, include_body: bool = True) -> dict:
        """转换为字典"""
        data = {
            "id": self.id,
            "account_id": self.account_id,
            "folder_id": self.folder_id,
            "uid": self.uid,
            "message_id": self.message_id,
            "thread_id": self.thread_id,
            "subject": self.subject,
            "from_name": self.from_name,
            "from_address": self.from_address,
            "to_addresses": self.to_addresses,
            "cc_addresses": self.cc_addresses,
            "bcc_addresses": self.bcc_addresses,
            "reply_to": self.reply_to,
            "is_read": self.is_read,
            "is_flagged": self.is_flagged,
            "is_deleted": self.is_deleted,
            "has_attachments": self.has_attachments,
            "attachments_count": self.attachments_count,
            "size_bytes": self.size_bytes,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "received_at": self.received_at.isoformat() if self.received_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_body:
            data["body_text"] = self.body_text
            data["body_html"] = self.body_html
            
        return data