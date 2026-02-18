"""
IMAP 同步服务 (支持 Password 和 OAuth2)
包含 Microsoft Graph API 支持 (用于绕过 IMAP 限制)
"""
import imaplib
import asyncio
import email
import logging
import socks
from urllib.parse import urlparse
from datetime import datetime, timedelta
from typing import Optional
import requests
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.email_account import EmailAccount, ProviderType, AuthType, AccountStatus
from app.models.email import Email
from app.models.folder import Folder
from app.models.setting import SystemSetting
from app.core.constants import (
    MICROSOFT_TOKEN_URL,
    GOOGLE_TOKEN_URL,
    GRAPH_URL,
    FOLDER_CONFIGS,
    IMAP_DEFAULT_PORT,
    IMAP_CONNECTION_TIMEOUT,
    IMAP_FETCH_LIMIT_DEFAULT
)
from app.services.sync_helpers import (
    decode_mime_header,
    parse_email_body,
    ensure_folder_exists,
    load_folders_cache,
    batch_check_existing_emails,
    truncate_email_fields
)

logger = logging.getLogger(__name__)

# 获取代理（账户优先，其次全局）
async def get_effective_proxy(account: EmailAccount, db: AsyncSession) -> Optional[str]:
    if account.proxy_url:
        return account.proxy_url
    # global proxy from system_settings
    result = await db.execute(select(SystemSetting).where(SystemSetting.key == "global_proxy"))
    setting = result.scalars().first()
    return setting.value if setting and setting.value else None

# IMAP Proxy Support
class ProxyIMAP4_SSL(imaplib.IMAP4_SSL):
    def __init__(self, host, port=imaplib.IMAP4_SSL_PORT, proxy_url=None):
        self.proxy_url = proxy_url
        # 只传递 IMAP4_SSL 支持的参数
        super().__init__(host, port)

    def _create_socket(self, timeout):
        if not self.proxy_url:
            return super()._create_socket(timeout)
        
        try:
            from urllib.parse import unquote
            parsed = urlparse(self.proxy_url)
            scheme = parsed.scheme.lower()
            
            proxy_type = None
            if 'socks5' in scheme:
                proxy_type = socks.SOCKS5
            elif 'socks4' in scheme:
                proxy_type = socks.SOCKS4
            elif 'http' in scheme:
                proxy_type = socks.HTTP
            
            if not proxy_type:
                return super()._create_socket(timeout)
                
            proxy_addr = parsed.hostname
            proxy_port = parsed.port
            # URL 解码用户名和密码（处理 %40 等编码字符）
            proxy_username = unquote(parsed.username) if parsed.username else None
            proxy_password = unquote(parsed.password) if parsed.password else None
            
            logger.info(f"[PROXY DEBUG] Connecting via {scheme}://{proxy_addr}:{proxy_port} (user: {proxy_username[:3] if proxy_username else 'none'}***)")
            
            sock = socks.socksocket()
            sock.set_proxy(proxy_type, proxy_addr, proxy_port, True, proxy_username, proxy_password)
            sock.settimeout(timeout)
            sock.connect((self.host, self.port))
            
            logger.info(f"[PROXY DEBUG] Successfully connected to {self.host}:{self.port} via proxy")
            
            if self.ssl_context:
                return self.ssl_context.wrap_socket(sock, server_hostname=self.host)
            else:
                import ssl
                context = ssl.create_default_context()
                return context.wrap_socket(sock, server_hostname=self.host)
        except Exception as e:
            logger.error(f"Proxy connection failed: {e}")
            raise

# OAuth2 Endpoints (已移到 constants.py)
# 保留这里是为了向后兼容，实际使用从 constants 导入
# MICROSOFT_TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
# GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
# GRAPH_URL = "https://graph.microsoft.com/v1.0"


async def _imap_login_and_fetch(account: EmailAccount, proxy_url: Optional[str], limit: int):
    """运行阻塞 IMAP 逻辑在线程池"""
    return await asyncio.to_thread(_imap_login_and_fetch_blocking, account, proxy_url, limit)


def _imap_login_and_fetch_blocking(account: EmailAccount, proxy_url: Optional[str], limit: int):
    imap_server = account.imap_server
    imap_port = account.imap_port or 993
    username = account.imap_username or account.email_address
    # 连接（统一使用 ProxyIMAP4_SSL，无代理时传 None）
    imap = ProxyIMAP4_SSL(imap_server, imap_port, proxy_url=proxy_url)

    # 认证
    if account.auth_type == AuthType.OAUTH2:
        new_token = _refresh_access_token(account, proxies={"http": proxy_url, "https": proxy_url} if proxy_url else None)
        if new_token:
            account.access_token = new_token
            account.token_expires_at = datetime.utcnow() + timedelta(hours=1)
            auth_string = _generate_xoauth2_string(username, new_token)
            imap.authenticate("XOAUTH2", lambda x: auth_string.encode("utf-8"))
        else:
            raise Exception("无法刷新 OAuth 令牌")
    else:
        if not account.imap_password:
            raise Exception("密码为空")
        imap.login(username, account.imap_password)

    # 同步收件箱和垃圾箱
    all_results = []
    
    # 根据服务器类型选择文件夹配置
    if imap_server and 'gmail' in imap_server.lower():
        folders_to_sync = FOLDER_CONFIGS["gmail"]
    else:
        folders_to_sync = FOLDER_CONFIGS["default"]
    
    for folder_path, folder_name, folder_type in folders_to_sync:
        try:
            imap.select(folder_path)
            typ, messages = imap.search(None, "ALL")
            if typ != "OK":
                continue
            
            email_ids = messages[0].split()
            fetch_ids = email_ids[-limit:] if limit > 0 else email_ids

            for eid in reversed(fetch_ids):
                try:
                    res, msg_data = imap.fetch(eid, "(RFC822)")
                    if res != "OK":
                        continue
                    raw_email = msg_data[0][1]
                    msg = email.message_from_bytes(raw_email)
                    # 附加文件夹信息
                    all_results.append((eid, msg, folder_path, folder_name, folder_type))
                except Exception:
                    continue
        except Exception as e:
            logger.warning(f"Failed to sync folder {folder_path}: {e}")
            continue

    imap.logout()
    return all_results

def _generate_xoauth2_string(username: str, access_token: str) -> str:
    """生成 SASL XOAUTH2 认证字符串"""
    auth_string = f"user={username}\x01auth=Bearer {access_token}\x01\x01"
    return auth_string

def _refresh_access_token(account: EmailAccount, proxies: Optional[dict] = None) -> Optional[str]:
    """使用 Refresh Token 换取新的 Access Token"""
    if not account.refresh_token or not account.client_id:
        logger.error(f"Account {account.id} missing refresh_token or client_id")
        return None

    token_url = ""
    data = {
        "client_id": account.client_id,
        "refresh_token": account.refresh_token,
        "grant_type": "refresh_token",
    }
    
    # 根据 Provider 选择 Endpoint
    if account.provider == ProviderType.MICROSOFT:
        token_url = MICROSOFT_TOKEN_URL
        if account.client_secret:
            data["client_secret"] = account.client_secret
        # Microsoft 默认 Scope (包含 IMAP 和 Graph)
        data["scope"] = "https://graph.microsoft.com/.default"
        
    elif account.provider == ProviderType.GOOGLE:
        token_url = GOOGLE_TOKEN_URL
        if account.client_secret:
            data["client_secret"] = account.client_secret
            
    else:
        # 对于其他 Provider，暂时不支持自动刷新
        return account.access_token

    try:
        response = requests.post(token_url, data=data, timeout=10, proxies=proxies)
        if response.status_code == 200:
            tokens = response.json()
            new_access_token = tokens.get("access_token")
            # 有些 Provider 会返回新的 refresh_token
            if tokens.get("refresh_token"):
                account.refresh_token = tokens.get("refresh_token")
            return new_access_token
        else:
            logger.error(f"Failed to refresh token: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error refreshing token: {e}")
        return None

def _decode_mime_header(header_value: Optional[str]) -> str:
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

async def sync_microsoft_graph(account: EmailAccount, db: AsyncSession, limit: int = 50, proxies: Optional[dict] = None) -> int:
    """
    使用 Microsoft Graph API 同步邮件 (绕过 IMAP)
    同步收件箱和垃圾箱
    """
    logger.info(f"Syncing via Graph API for {account.email_address}")
    
    # 1. 刷新 Token
    new_token = _refresh_access_token(account, proxies=proxies)
    if not new_token:
        account.status = AccountStatus.AUTH_REQUIRED
        account.status_message = "无法刷新 Token (Graph API)"
        await db.commit()
        return 0
        
    account.access_token = new_token
    account.token_expires_at = datetime.utcnow() + timedelta(hours=1)
    
    # 2. 调用 Graph API 获取邮件
    headers = {
        "Authorization": f"Bearer {new_token}",
        "Content-Type": "application/json"
    }
    
    # 使用配置中的文件夹
    folders_to_sync = FOLDER_CONFIGS["microsoft"]
    
    total_new_count = 0
    
    # 预加载文件夹缓存
    folders_cache = await load_folders_cache(db, account.id)
    
    for folder_path, folder_name, folder_type in folders_to_sync:
        try:
            # 使用辅助函数确保文件夹存在
            if folder_path in folders_cache:
                folder = folders_cache[folder_path]
            else:
                folder = await ensure_folder_exists(db, account.id, folder_path, folder_name, folder_type)
                folders_cache[folder_path] = folder
                
            url = f"{GRAPH_URL}/me/mailFolders/{folder_path}/messages"
            params = {
                "$top": limit,
                "$orderby": "receivedDateTime desc",
                "$select": "id,subject,from,toRecipients,ccRecipients,bccRecipients,replyTo,body,isRead,hasAttachments,receivedDateTime,createdDateTime"
            }
            
            async with httpx.AsyncClient(proxy=proxies.get("http://") if proxies else None) as client:
                resp = await client.get(url, headers=headers, params=params, timeout=30.0)
                
                if resp.status_code != 200:
                    logger.warning(f"Graph API Error for folder {folder_path}: {resp.status_code}")
                    continue
                    
                data = resp.json()
                messages = data.get("value", [])
                
                new_count = 0
                for msg in messages:
                    message_id = msg.get("id")
                    
                    # 查重
                    exists = await db.execute(select(Email).where(
                        Email.account_id == account.id,
                        Email.message_id == message_id
                    ))
                    if exists.scalars().first():
                        continue
                        
                    # 解析字段
                    subject = msg.get("subject") or "(无主题)"
                    from_addr = msg.get("from", {}).get("emailAddress", {}).get("address", "")
                    from_name = msg.get("from", {}).get("emailAddress", {}).get("name", "")
                    
                    # 收件人列表
                    to_addrs = []
                    for recipient in msg.get("toRecipients", []):
                        addr = recipient.get("emailAddress", {}).get("address")
                        if addr: to_addrs.append(addr)
                    to_str = ", ".join(to_addrs)
                    
                    # Body
                    body_content = msg.get("body", {}).get("content", "")
                    body_type = msg.get("body", {}).get("contentType", "text").lower()
                    
                    body_html = body_content if body_type == "html" else None
                    body_text = body_content if body_type == "text" else None
                    
                    # 时间
                    received_str = msg.get("receivedDateTime")
                    received_at = datetime.fromisoformat(received_str.replace("Z", "+00:00")) if received_str else datetime.utcnow()
                    
                    new_email = Email(
                        account_id=account.id,
                        folder_id=folder.id,
                        uid=message_id, # Graph API ID 作为 UID
                        message_id=message_id,
                        subject=subject[:255],
                        from_name=from_name[:100],
                        from_address=from_addr[:255],
                        to_addresses=to_str[:1000],
                        body_text=body_text[:5000] if body_text else None,
                        body_html=body_html[:10000] if body_html else None,
                        received_at=received_at,
                        is_read=msg.get("isRead", False),
                        has_attachments=msg.get("hasAttachments", False)
                    )
                    db.add(new_email)
                    new_count += 1
                
                total_new_count += new_count
                logger.info(f"Synced {new_count} emails from folder {folder_path}")
                
        except Exception as e:
            logger.warning(f"Failed to sync folder {folder_path}: {e}")
            continue
    
    account.status = AccountStatus.ACTIVE
    account.status_message = "正常 (API)"
    account.last_sync_at = datetime.utcnow()
    await db.commit()
    return total_new_count



async def sync_emails(account_id: int, db: AsyncSession, limit: int = 50) -> int:
    """
    同步指定账户的邮件 (自动分发 IMAP 或 Graph API)
    """
    result = await db.execute(select(EmailAccount).where(EmailAccount.id == account_id))
    account = result.scalars().first()
    if not account or account.status == AccountStatus.DISABLED:
        return 0

    proxy_url = await get_effective_proxy(account, db)
    proxies = {"http://": proxy_url, "https://": proxy_url} if proxy_url else None
    
    logger.info(f"[PROXY CHECK] Account {account.id} ({account.email_address}) - Proxy URL: {proxy_url}")

    if account.provider == ProviderType.MICROSOFT and account.auth_type == AuthType.OAUTH2:
        logger.info(f"[PROXY CHECK] Using Graph API with proxies: {proxies}")
        return await sync_microsoft_graph(account, db, limit, proxies=proxies)

    try:
        fetched = await _imap_login_and_fetch(account, proxy_url, limit)
        # 同步成功，更新状态为 ACTIVE
        account.status = AccountStatus.ACTIVE
        account.status_message = "正常"
        await db.commit()
    except Exception as e:
        logger.error(f"IMAP error: {e}")
        account.status = AccountStatus.ERROR
        account.status_message = f"连接失败: {str(e)}"
        await db.commit()
        return 0

    if not fetched:
        return 0

    new_count = 0
    for eid, msg, folder_path, folder_name, folder_type in fetched:
        try:
            # 确保文件夹存在
            folder_res = await db.execute(select(Folder).where(
                Folder.account_id == account.id, Folder.path == folder_path
            ))
            folder = folder_res.scalars().first()
            if not folder:
                folder = Folder(
                    account_id=account.id,
                    name=folder_name,
                    path=folder_path,
                    is_system=True,
                    folder_type=folder_type
                )
                db.add(folder)
                await db.commit()
                await db.refresh(folder)
            
            message_id = msg.get("Message-ID", "").strip() or f"{account.id}-{eid.decode()}"
            exists = await db.execute(select(Email).where(
                Email.account_id == account.id,
                Email.message_id == message_id
            ))
            if exists.scalars().first():
                continue

            subject = _decode_mime_header(msg.get("Subject"))
            from_header = _decode_mime_header(msg.get("From"))
            to_header = _decode_mime_header(msg.get("To"))

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
                            except:
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
                    except:
                        pass

            new_email = Email(
                account_id=account.id,
                folder_id=folder.id,
                uid=eid.decode(),
                message_id=message_id,
                subject=subject[:255] if subject else "(无主题)",
                from_address=from_header[:255] if from_header else "",
                to_addresses=to_header[:1000] if to_header else "",
                body_text=body_text[:5000] if body_text else None,
                body_html=body_html[:10000] if body_html else None,
                received_at=datetime.utcnow(),
                is_read=False
            )
            db.add(new_email)
            new_count += 1
        except Exception as e:
            logger.error(f"Error parsing email {eid}: {e}")
            continue

    account.last_sync_at = datetime.utcnow()
    await db.commit()
    return new_count

async def sync_account_task(account_id: int):
    """
    后台任务包装器：创建独立的数据库会话并执行同步
    """
    async with AsyncSessionLocal() as db:
        try:
            logger.info(f"Starting background sync for account {account_id}")
            count = await sync_emails(account_id, db)
            logger.info(f"Background sync finished for account {account_id}: {count} emails")
        except Exception as e:
            logger.error(f"Background sync failed for account {account_id}: {e}")
