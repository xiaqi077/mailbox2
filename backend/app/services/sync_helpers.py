"""
同步辅助函数 - 提取公共逻辑
"""
import email
from typing import Optional, Tuple, List, Dict
from email.header import decode_header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.folder import Folder
from app.models.email import Email
from app.core.constants import (
    MAX_SUBJECT_LENGTH,
    MAX_FROM_ADDRESS_LENGTH,
    MAX_FROM_NAME_LENGTH,
    MAX_TO_ADDRESSES_LENGTH,
    MAX_BODY_TEXT_LENGTH,
    MAX_BODY_HTML_LENGTH
)


def decode_mime_header(header_value: Optional[str]) -> str:
    """解码 MIME 头部"""
    if not header_value:
        return ""
    decoded_parts = decode_header(header_value)
    result = []
    for content, encoding in decoded_parts:
        if isinstance(content, bytes):
            try:
                result.append(content.decode(encoding or "utf-8", errors="ignore"))
            except LookupError:
                result.append(content.decode("utf-8", errors="ignore"))
        else:
            result.append(str(content))
    return "".join(result)


def parse_email_body(msg: email.message.Message) -> Tuple[str, str]:
    """
    解析邮件正文
    返回: (body_text, body_html)
    """
    body_text = ""
    body_html = ""
    
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            if "attachment" not in content_disposition:
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    try:
                        decoded = payload.decode(charset, errors="ignore")
                        if content_type == "text/html":
                            body_html += decoded
                        else:
                            body_text += decoded
                    except Exception:
                        pass
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            try:
                decoded = payload.decode(charset, errors="ignore")
                if msg.get_content_type() == "text/html":
                    body_html = decoded
                else:
                    body_text = decoded
            except Exception:
                pass
    
    return body_text, body_html


async def ensure_folder_exists(
    db: AsyncSession,
    account_id: int,
    folder_path: str,
    folder_name: str,
    folder_type: str
) -> Folder:
    """
    确保文件夹存在，不存在则创建
    返回: Folder 对象
    """
    folder_res = await db.execute(select(Folder).where(
        Folder.account_id == account_id,
        Folder.path == folder_path
    ))
    folder = folder_res.scalars().first()
    
    if not folder:
        folder = Folder(
            account_id=account_id,
            name=folder_name,
            path=folder_path,
            is_system=True,
            folder_type=folder_type
        )
        db.add(folder)
        await db.commit()
        await db.refresh(folder)
    
    return folder


async def load_folders_cache(db: AsyncSession, account_id: int) -> Dict[str, Folder]:
    """
    加载账户的所有文件夹到缓存
    返回: {folder_path: Folder} 字典
    """
    result = await db.execute(
        select(Folder).where(Folder.account_id == account_id)
    )
    folders = result.scalars().all()
    return {folder.path: folder for folder in folders}


async def batch_check_existing_emails(
    db: AsyncSession,
    account_id: int,
    message_ids: List[str]
) -> set:
    """
    批量检查邮件是否已存在
    返回: 已存在的 message_id 集合
    """
    if not message_ids:
        return set()
    
    result = await db.execute(
        select(Email.message_id).where(
            Email.account_id == account_id,
            Email.message_id.in_(message_ids)
        )
    )
    existing = result.scalars().all()
    return set(existing)


def truncate_email_fields(
    subject: str,
    from_name: str,
    from_address: str,
    to_addresses: str,
    body_text: str,
    body_html: str
) -> Tuple[str, str, str, str, str, str]:
    """
    截断邮件字段到合适的长度
    返回: (subject, from_name, from_address, to_addresses, body_text, body_html)
    """
    return (
        subject[:MAX_SUBJECT_LENGTH] if subject else "(无主题)",
        from_name[:MAX_FROM_NAME_LENGTH] if from_name else "",
        from_address[:MAX_FROM_ADDRESS_LENGTH] if from_address else "",
        to_addresses[:MAX_TO_ADDRESSES_LENGTH] if to_addresses else "",
        body_text[:MAX_BODY_TEXT_LENGTH] if body_text else None,
        body_html[:MAX_BODY_HTML_LENGTH] if body_html else None
    )
