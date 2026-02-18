from typing import List, Optional, Generic, TypeVar
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, desc
from pydantic import BaseModel
from pydantic.generics import GenericModel
import csv
import io
import re

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.email import Email
from app.models.email_account import EmailAccount, ProviderType, AccountStatus, AuthType
from app.services.imap_sync import sync_emails, sync_account_task

router = APIRouter()

T = TypeVar("T")

class ApiResponse(GenericModel, Generic[T]):
    success: bool
    data: T
    message: Optional[str] = None

# Schema 定义
class CreateAccountSchema(BaseModel):
    email_address: str
    provider: ProviderType
    auth_type: AuthType = AuthType.PASSWORD
    display_name: Optional[str] = None
    
    # IMAP Password 模式
    imap_server: Optional[str] = None
    imap_port: int = 993
    imap_use_ssl: bool = True
    username: Optional[str] = None
    password: Optional[str] = None
    
    # OAuth2 模式
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    refresh_token: Optional[str] = None
    access_token: Optional[str] = None
    
    # 代理设置
    proxy_url: Optional[str] = None

class UpdateAccountSchema(BaseModel):
    email_address: Optional[str] = None
    display_name: Optional[str] = None
    provider: Optional[ProviderType] = None
    
    # 代理设置
    proxy_url: Optional[str] = None
    
    # 更新密码或 Token
    password: Optional[str] = None
    refresh_token: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    
    # 更新 IMAP 配置
    imap_server: Optional[str] = None
    imap_port: Optional[int] = None

class AccountResponse(BaseModel):
    id: int
    email_address: str
    display_name: Optional[str]
    provider: str
    auth_type: str
    status: str
    status_message: Optional[str]
    total_emails: int
    unread_count: int
    last_sync_at: Optional[str]
    # OAuth 详情 (仅在编辑时需要回显部分)
    client_id: Optional[str] = None
    imap_server: Optional[str] = None
    imap_port: Optional[int] = None
    imap_username: Optional[str] = None
    proxy_url: Optional[str] = None
    
    class Config:
        from_attributes = True


class AccountExportResponse(BaseModel):
    """完整账户导出响应（包含所有敏感信息用于备份）"""
    id: int
    email_address: str
    display_name: Optional[str] = None
    provider: str
    auth_type: str = 'password'
    status: str = 'active'
    
    # IMAP 配置
    imap_server: Optional[str] = None
    imap_port: int = 993
    imap_use_ssl: bool = True
    imap_username: Optional[str] = None
    imap_password: Optional[str] = None
    
    # OAuth2 配置
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    refresh_token: Optional[str] = None
    access_token: Optional[str] = None
    token_expires_at: Optional[str] = None
    
    # 其他配置
    proxy_url: Optional[str] = None
    sync_enabled: bool = True
    
    class Config:
        from_attributes = True

@router.get("/default-credentials")
async def get_default_credentials(
    provider: ProviderType,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取指定 Provider 的最近一次使用的 Client ID / Secret
    用于前端自动填充
    """
    stmt = select(EmailAccount).where(
        EmailAccount.user_id == current_user.id,
        EmailAccount.provider == provider,
        EmailAccount.auth_type == AuthType.OAUTH2,
        EmailAccount.client_id.isnot(None)
    ).order_by(EmailAccount.updated_at.desc()).limit(1)
    
    result = await db.execute(stmt)
    account = result.scalars().first()
    
    if account:
        return {
            "client_id": account.client_id,
            "client_secret": account.client_secret
        }
    return {}

# 批量导入接口
@router.post("/batch-import", status_code=status.HTTP_201_CREATED)
async def batch_import_accounts(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """批量导入账户 (CSV)"""
    if not file.filename.endswith('.csv') and not file.filename.endswith('.txt'):
        raise HTTPException(status_code=400, detail="仅支持 CSV 或 TXT 文件")
    
    content = await file.read()
    try:
        # 解析 CSV
        decoded = content.decode('utf-8-sig') # 处理 BOM
        rows = []
        
        if "----" in decoded:
            # 自定义格式: email----password----client_id----refresh_token
            for line in decoded.splitlines():
                if not line.strip(): continue
                parts = line.split("----")
                if len(parts) >= 4:
                    rows.append({
                        "email_address": parts[0].strip(),
                        "password": parts[1].strip(),
                        "client_id": parts[2].strip(),
                        "refresh_token": parts[3].strip(),
                        "provider": "microsoft",
                        "imap_server": "outlook.office365.com",
                        "imap_port": 993,
                        "username": parts[0].strip()
                    })
        else:
            reader = csv.DictReader(io.StringIO(decoded))
            rows = list(reader)
        
        imported_count = 0
        errors = []
        new_account_ids = []
        
        for row in rows:
            email = row.get('email_address', '').strip()
            if not email:
                continue
                
            # 查重
            exists = await db.execute(select(EmailAccount).where(
                EmailAccount.user_id == current_user.id,
                EmailAccount.email_address == email
            ))
            if exists.scalars().first():
                errors.append(f"{email}: 已存在")
                continue
                
            # 构造账户
            provider_str = row.get('provider', 'imap').lower()
            try:
                provider = ProviderType(provider_str)
            except:
                provider = ProviderType.IMAP
                
            new_account = EmailAccount(
                user_id=current_user.id,
                email_address=email,
                display_name=email.split('@')[0],
                provider=provider,
                status=AccountStatus.ACTIVE,
                imap_server=row.get('imap_server'),
                imap_port=int(row.get('imap_port') or 993),
                imap_username=row.get('username') or email
            )
            
            # 区分 Password / OAuth
            refresh_token = row.get('refresh_token')
            password = row.get('password')
            
            if refresh_token:
                new_account.auth_type = AuthType.OAUTH2
                new_account.refresh_token = refresh_token
                new_account.client_id = row.get('client_id')
                new_account.client_secret = row.get('client_secret')
                
                # 如果没填 imap_server，尝试自动推断
                if not new_account.imap_server:
                    if provider == ProviderType.MICROSOFT:
                        new_account.imap_server = "outlook.office365.com"
                    elif provider == ProviderType.GOOGLE:
                        new_account.imap_server = "imap.gmail.com"
                        
            elif password:
                new_account.auth_type = AuthType.PASSWORD
                new_account.imap_password = password
            else:
                errors.append(f"{email}: 缺少认证信息 (password 或 refresh_token)")
                continue
                
            db.add(new_account)
            await db.flush()  # 获取 ID
            new_account_ids.append(new_account.id)
            imported_count += 1
            
        await db.commit()
        
        # 触发后台同步
        if background_tasks and new_account_ids:
            for acc_id in new_account_ids:
                background_tasks.add_task(sync_account_task, acc_id)
        
        return {
            "success": True, 
            "imported": imported_count, 
            "errors": errors
        }

        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"解析失败: {str(e)}")

# API 路由
@router.post("/", response_model=ApiResponse[AccountResponse], status_code=status.HTTP_201_CREATED)
async def create_account(
    account_in: CreateAccountSchema,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """添加邮箱账户"""
    # 检查是否已存在
    result = await db.execute(
        select(EmailAccount).where(
            EmailAccount.user_id == current_user.id,
            EmailAccount.email_address == account_in.email_address
        )
    )
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该邮箱账户已存在"
        )
    
    # 自动推断 IMAP 服务器 (如果未提供)
    imap_server = account_in.imap_server
    if not imap_server and account_in.provider == ProviderType.GOOGLE:
        imap_server = "imap.gmail.com"
    elif not imap_server and account_in.provider == ProviderType.MICROSOFT:
        imap_server = "outlook.office365.com"
    
    # 创建账户对象
    new_account = EmailAccount(
        user_id=current_user.id,
        email_address=account_in.email_address,
        display_name=account_in.display_name or account_in.email_address.split('@')[0],
        provider=account_in.provider,
        auth_type=account_in.auth_type,
        
        # IMAP 配置
        imap_server=imap_server,
        imap_port=account_in.imap_port,
        imap_use_ssl=account_in.imap_use_ssl,
        imap_username=account_in.username or account_in.email_address,
        imap_password=account_in.password, # 注意：实际生产中应加密存储
        
        # OAuth 配置
        client_id=account_in.client_id,
        client_secret=account_in.client_secret,
        refresh_token=account_in.refresh_token,
        access_token=account_in.access_token,
        
        # 代理设置
        proxy_url=account_in.proxy_url,
        
        status=AccountStatus.ACTIVE
    )
    
    db.add(new_account)
    await db.commit()
    await db.refresh(new_account)
    
    # 触发后台同步
    background_tasks.add_task(sync_account_task, new_account.id)
    
    # 返回统一格式（使用 to_dict() 而不是 include_credentials）
    account_dict = new_account.to_dict()
    return {"success": True, "data": account_dict}

@router.get("/export", response_model=ApiResponse[List[AccountExportResponse]])
async def export_accounts(
    limit: int = 1000,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """导出账户（包含敏感字段）"""
    result = await db.execute(
        select(EmailAccount)
        .where(EmailAccount.user_id == current_user.id)
        .limit(limit)
    )
    accounts = result.scalars().all()
    return {"success": True, "data": [{
        "id": acc.id,
        "email_address": acc.email_address,
        "display_name": acc.display_name,
        "provider": acc.provider.value,
        "auth_type": acc.auth_type.value,
        "status": acc.status.value,
        "imap_server": acc.imap_server,
        "imap_port": acc.imap_port,
        "imap_use_ssl": acc.imap_use_ssl,
        "imap_username": acc.imap_username,
        "imap_password": acc.imap_password,
        "client_id": acc.client_id,
        "client_secret": acc.client_secret,
        "refresh_token": acc.refresh_token,
        "access_token": acc.access_token,
        "token_expires_at": acc.token_expires_at.isoformat() if acc.token_expires_at else None,
        "proxy_url": acc.proxy_url,
        "sync_enabled": acc.sync_enabled,
    } for acc in accounts]}

@router.get("/", response_model=ApiResponse[List[AccountResponse]])
async def list_accounts(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取账户列表"""
    result = await db.execute(
        select(EmailAccount)
        .where(EmailAccount.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
    )
    accounts = result.scalars().all()
    # 正常模式：返回安全数据（不包含敏感信息）
    return {"success": True, "data": [acc.to_dict(include_credentials=False) for acc in accounts]}

@router.get("/{account_id}", response_model=ApiResponse[AccountResponse])
async def get_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取单个账户详情"""
    result = await db.execute(
        select(EmailAccount).where(
            EmailAccount.id == account_id,
            EmailAccount.user_id == current_user.id
        )
    )
    account = result.scalars().first()
    if not account:
        raise HTTPException(status_code=404, detail="账户不存在")
    return {"success": True, "data": account.to_dict(include_credentials=True)}

@router.put("/{account_id}", response_model=ApiResponse[AccountResponse])
async def update_account(
    account_id: int,
    account_in: UpdateAccountSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新账户"""
    result = await db.execute(
        select(EmailAccount).where(
            EmailAccount.id == account_id,
            EmailAccount.user_id == current_user.id
        )
    )
    account = result.scalars().first()
    if not account:
        raise HTTPException(status_code=404, detail="账户不存在")
    
    if account_in.email_address:
        account.email_address = account_in.email_address
    if account_in.display_name:
        account.display_name = account_in.display_name
    if account_in.provider:
        account.provider = account_in.provider
        
    # 密码更新
    if account_in.password:
        account.imap_password = account_in.password
        account.auth_type = AuthType.PASSWORD
        
    # OAuth 更新
    if account_in.refresh_token:
        account.refresh_token = account_in.refresh_token
        account.auth_type = AuthType.OAUTH2
    if account_in.client_id:
        account.client_id = account_in.client_id
    if account_in.client_secret:
        account.client_secret = account_in.client_secret
        
    # Server 更新
    if account_in.imap_server:
        account.imap_server = account_in.imap_server
    if account_in.imap_port:
        account.imap_port = account_in.imap_port
        
    if account_in.proxy_url is not None:
        account.proxy_url = account_in.proxy_url if account_in.proxy_url else None

    await db.commit()
    await db.refresh(account)
    return {"success": True, "data": account.to_dict(include_credentials=True)}

@router.post("/{account_id}/sync", status_code=status.HTTP_200_OK)
async def sync_account(
    account_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """手动触发同步"""
    # 检查账户是否存在且属于当前用户
    result = await db.execute(
        select(EmailAccount).where(
            EmailAccount.id == account_id,
            EmailAccount.user_id == current_user.id
        )
    )
    account = result.scalars().first()
    if not account:
        raise HTTPException(status_code=404, detail="账户不存在")
    
    # 触发后台任务
    background_tasks.add_task(sync_account_task, account.id)
    
    return {"success": True, "message": "已触发后台同步"}

@router.delete("/{account_id}")
async def delete_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """删除账户"""
    result = await db.execute(
        select(EmailAccount).where(
            EmailAccount.id == account_id,
            EmailAccount.user_id == current_user.id
        )
    )
    account = result.scalars().first()
    if not account:
        raise HTTPException(status_code=404, detail="账户不存在")
    
    await db.delete(account)
    await db.commit()
    
    return {"success": True, "message": "删除成功"}

@router.get("/{account_id}/latest-code", summary="获取最新验证码")
async def get_latest_code(
    account_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取最新验证码"""
    # 检查权限
    result = await db.execute(
        select(EmailAccount).where(
            EmailAccount.id == account_id,
            EmailAccount.user_id == current_user.id
        )
    )
    if not result.scalars().first():
        raise HTTPException(status_code=404, detail="账户不存在")
        
    # 查询最近邮件
    stmt = (
        select(Email)
        .where(Email.account_id == account_id)
        .order_by(desc(Email.received_at))
        .limit(30)
    )
    emails = (await db.execute(stmt)).scalars().all()
    
    # 正则：匹配 4-8 位数字 (支持 G- 前缀，支持中间有空格)
    # 使用 \b 边界匹配，兼容 :123456 和 G-123456
    code_pattern = re.compile(r'\b(\d{3,4}\s?\d{3,4}|\d{4,8})\b')
    
    # 辅助函数：去除 HTML 标签
    def strip_html(html_str):
        if not html_str: return ""
        return re.sub(r'<[^>]+>', ' ', html_str)

    keywords = ['code', '验证码', 'verification', 'security', '登录', '确认', 'captcha']
    
    for email in emails:
        # 拼接所有可能包含验证码的区域：主题 + 纯文本 + HTML(去标签)
        content_parts = [email.subject or ""]
        if email.body_text:
            content_parts.append(email.body_text)
        if email.body_html:
            content_parts.append(strip_html(email.body_html))
            
        full_content = " ".join(content_parts)
        
        # 检查关键词
        if any(k in full_content.lower() for k in keywords):
            match = code_pattern.search(full_content)
            if match:
                # 提取数字（去掉空格）
                code_val = match.group().replace(' ', '')
                # 如果匹配的是 G- 后面的，不需要处理，因为 regex 只捕获了数字部分
                # 但 regex group() 捕获的是 () 内的内容吗？
                # re.search 返回 match object. match.group() 返回整个匹配串 (Group 0).
                # 如果有括号，match.group(1) 返回第一个括号内容。
                # 我的 regex: (\d...|\d...) 是 Group 1.
                # 所以应该用 match.group(1) 或者 match.group() 如果整个 regex 是捕获组。
                # 我的 regex: (?:...)(\d...)
                # 第一个是 non-capturing group. 第二个是 capturing group.
                # 所以 match.group(1) 是数字部分。
                # 但 match.group() (默认0) 是整个匹配到的字符串。
                # 如果 regex 匹配 "123456"，group(0) 是 "123456"。
                # 如果 regex 匹配 "123 456"，group(0) 是 "123 456"。
                
                # Wait, match.group() returns whole match.
                # My regex lookbehind (?<=G-) is zero-width assertion.
                # So if input is "G-123456", match is "123456".
                # So match.group() is correct.
                
                return {
                    "success": True,
                    "code": code_val,
                    "email_subject": email.subject,
                    "received_at": email.received_at
                }
                
    return {"success": False, "code": None}
