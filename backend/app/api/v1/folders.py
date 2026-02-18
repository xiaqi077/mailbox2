"""
文件夹 API 路由
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.models.folder import Folder
from app.models.email_account import EmailAccount
from app.api.deps import get_current_active_user

router = APIRouter()

@router.get("/", summary="获取文件夹列表")
async def list_folders(
    account_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取当前用户的文件夹列表"""
    # 基础查询：关联账户表，筛选属于当前用户的账户
    stmt = (
        select(Folder)
        .join(EmailAccount, Folder.account_id == EmailAccount.id)
        .where(EmailAccount.user_id == current_user.id)
    )
    
    if account_id:
        stmt = stmt.where(Folder.account_id == account_id)
    
    stmt = stmt.order_by(Folder.id)
    
    result = await db.execute(stmt)
    folders = result.scalars().all()
    
    return {
        "success": True,
        "data": [
            {
                "id": f.id,
                "account_id": f.account_id,
                "name": f.name,
                "path": f.path,
                "folder_type": f.folder_type,
                "is_system": f.is_system,
                "total_count": f.total_count,
                "unread_count": f.unread_count,
                "last_sync_at": f.last_sync_at.isoformat() if f.last_sync_at else None,
            }
            for f in folders
        ]
    }