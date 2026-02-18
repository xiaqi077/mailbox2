from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.setting import SystemSetting
from app.models.user import User
from app.api.deps import get_current_active_superuser

router = APIRouter()

class SettingSchema(BaseModel):
    value: Optional[str] = None

@router.get("/{key}", summary="获取设置")
async def get_setting(key: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(SystemSetting).where(SystemSetting.key == key))
    setting = res.scalar_one_or_none()
    return {"success": True, "data": {"key": key, "value": setting.value if setting else None}}

@router.put("/{key}", summary="更新设置")
async def update_setting(
    key: str, 
    payload: SettingSchema, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    """更新系统设置（仅管理员）"""
    res = await db.execute(select(SystemSetting).where(SystemSetting.key == key))
    setting = res.scalar_one_or_none()
    
    val = payload.value or ""
    
    if not setting:
        setting = SystemSetting(key=key, value=val)
        db.add(setting)
    else:
        setting.value = val
        
    await db.commit()
    return {"key": key, "value": val}
