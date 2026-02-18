"""
用户管理 API 路由
"""
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.security import get_password_hash
from app.models.user import User
from app.api.deps import get_current_user, get_current_active_user # 从 deps 引入

router = APIRouter()


@router.get("/", summary="获取用户列表（管理员）")
async def list_users(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取用户列表（仅管理员）"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    
    # 构建查询
    query = select(User)
    
    if search:
        query = query.where(
            (User.username.ilike(f"%{search}%")) |
            (User.email.ilike(f"%{search}%")) |
            (User.full_name.ilike(f"%{search}%"))
        )
    
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    
    # 获取总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 分页查询
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    users = result.scalars().all()
    
    return {
        "success": True,
        "data": [user.to_dict() for user in users],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size
        }
    }


@router.get("/me", summary="获取当前用户信息")
async def get_me(current_user: User = Depends(get_current_active_user)):
    """获取当前登录用户的详细信息"""
    return {
        "success": True,
        "data": current_user.to_dict()
    }


@router.put("/me", summary="更新当前用户信息")
async def update_me(
    username: Optional[str] = None,
    full_name: Optional[str] = None,
    email: Optional[str] = None,
    avatar_url: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新当前用户的信息"""
    if username is not None and username != current_user.username:
        # 检查用户名是否已被使用
        result = await db.execute(select(User).where(User.username == username))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )
        current_user.username = username

    if full_name is not None:
        current_user.full_name = full_name
    
    if email is not None and email != current_user.email:
        # 检查邮箱是否已被使用
        result = await db.execute(select(User).where(User.email == email))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被使用"
            )
        current_user.email = email
    
    if avatar_url is not None:
        current_user.avatar_url = avatar_url
    
    await db.commit()
    await db.refresh(current_user)
    
    return {
        "success": True,
        "data": current_user.to_dict()
    }


@router.get("/{user_id}", summary="获取用户详情（管理员）")
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取指定用户的详细信息（仅管理员或本人）"""
    if not current_user.is_superuser and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限查看此用户信息"
        )
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return {
        "success": True,
        "data": user.to_dict()
    }


@router.put("/{user_id}", summary="更新用户信息（管理员）")
async def update_user(
    user_id: int,
    is_active: Optional[bool] = None,
    is_superuser: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新指定用户的信息（仅管理员）"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    if is_active is not None:
        user.is_active = is_active
    
    if is_superuser is not None:
        user.is_superuser = is_superuser
    
    await db.commit()
    await db.refresh(user)
    
    return {
        "success": True,
        "data": user.to_dict()
    }


@router.delete("/{user_id}", summary="删除用户（管理员）")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """删除指定用户（仅管理员，不能删除自己）"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己的账号"
        )
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    await db.delete(user)
    await db.commit()
    
    return {
        "success": True,
        "message": "用户已删除"
    }
