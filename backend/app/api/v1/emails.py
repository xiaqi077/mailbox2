"""
邮件 API 路由
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func, desc, or_, delete, update
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.models.email import Email
from app.models.email_account import EmailAccount
from app.api.deps import get_current_active_user  # 从 deps 引入

router = APIRouter()


@router.get("/", summary="获取邮件列表")
async def list_emails(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    account_id: Optional[int] = None,
    folder_id: Optional[int] = None,
    is_read: Optional[bool] = None,
    is_flagged: Optional[bool] = None,
    is_deleted: Optional[bool] = Query(False), # 默认只显示未删除的
    has_attachments: Optional[bool] = None,
    q: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取当前用户的邮件列表"""
    # 基础查询：关联账户表，筛选属于当前用户的账户
    stmt = (
        select(Email)
        .join(EmailAccount, Email.account_id == EmailAccount.id)
        .where(EmailAccount.user_id == current_user.id)
    )

    if account_id:
        stmt = stmt.where(Email.account_id == account_id)
    if folder_id:
        stmt = stmt.where(Email.folder_id == folder_id)
    if is_read is not None:
        stmt = stmt.where(Email.is_read == is_read)
    if is_flagged is not None:
        stmt = stmt.where(Email.is_flagged == is_flagged)
    if is_deleted is not None:
        stmt = stmt.where(Email.is_deleted == is_deleted)
    if has_attachments is not None:
        stmt = stmt.where(Email.has_attachments == has_attachments)
    if q:
        search_filter = or_(
            Email.subject.ilike(f"%{q}%"),
            Email.from_address.ilike(f"%{q}%"),
            Email.from_name.ilike(f"%{q}%")
        )
        stmt = stmt.where(search_filter)

    # 计算总数 (由于 join 可能会复杂，这里简化处理，或者分两步)
    # 正规写法是 subquery count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    # 排序分页
    stmt = stmt.order_by(desc(Email.received_at), desc(Email.created_at))
    stmt = stmt.options(selectinload(Email.account))
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(stmt)
    emails = result.scalars().all()
    
    data = []
    for e in emails:
        d = e.to_dict(include_body=False)
        if e.account:
            d['account_email'] = e.account.email_address
            # 处理 Enum
            d['account_provider'] = getattr(e.account.provider, 'value', str(e.account.provider))
        data.append(d)

    return {
        "success": True,
        "data": data,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0
        }
    }


@router.delete("/clear", summary="清空邮件")
async def clear_emails(
    account_id: int,
    is_trash: bool = False,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """清空指定账户的收件箱或垃圾箱（仅删除数据库记录）"""
    # 验证账户归属
    result = await db.execute(select(EmailAccount).where(EmailAccount.id == account_id, EmailAccount.user_id == current_user.id))
    if not result.scalars().first():
        raise HTTPException(status_code=404, detail="账户不存在")
        
    if is_trash:
        # 清空垃圾箱：删除所有标记为 is_deleted=True 的邮件
        stmt = delete(Email).where(Email.account_id == account_id, Email.is_deleted == True)
        res = await db.execute(stmt)
        count = res.rowcount
        await db.commit()
        return {"success": True, "message": f"已彻底清除 {count} 封垃圾邮件"}
    else:
        # 清空收件箱：将所有 is_deleted=False 的邮件标记为 is_deleted=True (移入垃圾箱)
        # 或者直接删除？用户说“清空”，通常意味着不再显示。
        # 如果是清空收件箱，应该移入垃圾箱？
        # 用户说“清空所有的邮件”，可能想彻底删除。
        # 但为了安全，先移入垃圾箱比较好？
        # 可是如果用户想彻底清空，移入垃圾箱还得再清一次。
        # 这里我做成：收件箱 -> 移入垃圾箱；垃圾箱 -> 彻底删除。
        
        # 将收件箱邮件标记为已删除
        stmt = update(Email).where(Email.account_id == account_id, Email.is_deleted == False).values(is_deleted=True)
        res = await db.execute(stmt)
        count = res.rowcount
        await db.commit()
        return {"success": True, "message": f"已将 {count} 封邮件移入垃圾箱"}

@router.get("/{email_id}", summary="获取邮件详情")
async def get_email(
    email_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取单封邮件详情（包含正文）"""
    stmt = (
        select(Email)
        .join(EmailAccount, Email.account_id == EmailAccount.id)
        .where(Email.id == email_id)
        .where(EmailAccount.user_id == current_user.id)
    )
    
    result = await db.execute(stmt)
    email = result.scalar_one_or_none()
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="邮件不存在"
        )
    return {"success": True, "data": email.to_dict(include_body=True)}
