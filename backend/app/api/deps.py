from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"/api/v1/auth/login"
)

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(reusable_oauth2)
) -> User:
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        token_data = payload.get("sub")
        if token_data is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无法验证凭证"
            )
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无法验证凭证"
        )
        
    # 查询用户 (token_data 是 email)
    # 注意：在 auth.py 的 login 里我们把 sub 设为了 user.email
    # 但之前可能是 user.id，这会导致兼容性问题。
    # 为了保险，先尝试用 email 查，查不到再尝试转 int 查 id
    
    # 既然这是新库，我们统一约定：sub 放 email
    result = await db.execute(select(User).where(User.email == token_data))
    user = result.scalars().first()
    
    # 如果没查到，可能是旧逻辑存的 ID？
    if not user:
        try:
            uid = int(token_data)
            result = await db.execute(select(User).where(User.id == uid))
            user = result.scalars().first()
        except (ValueError, TypeError):
            pass
            
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
        
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="用户未激活")
    return current_user

async def get_current_active_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=400, detail="权限不足"
        )
    return current_user
