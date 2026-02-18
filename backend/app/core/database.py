"""
数据库模块 - SQLAlchemy 配置和连接管理
"""
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine
)
from sqlalchemy.orm import declarative_base
from sqlalchemy import text, select

from app.core.config import settings

# 创建异步引擎
engine = create_async_engine(
    settings.async_database_url,
    echo=settings.debug,  # 调试模式下显示SQL语句
    future=True,
    pool_pre_ping=True,  # 连接池健康检查
    pool_recycle=3600,   # 连接回收时间
)

# 异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

# 声明性基类
Base = declarative_base()


async def init_db():
    """初始化数据库 - 创建所有表 + 预置管理员账号"""
    # 必须在此导入所有模型，确保 Base.metadata 能识别到它们
    from app.models.user import User
    from app.models.email_account import EmailAccount
    from app.models.email import Email
    from app.models.folder import Folder
    from app.models.setting import SystemSetting
    from app.core.security import get_password_hash

    async with engine.begin() as conn:
        # 开启 WAL 模式 (Write-Ahead Logging) 以提升并发性能
        try:
            await conn.execute(text("PRAGMA journal_mode=WAL"))
            await conn.execute(text("PRAGMA synchronous=NORMAL"))
        except Exception:
            pass

        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)
        
        # 针对旧数据库的手动迁移 (如果存在的话)
        try:
            result = await conn.execute(text("PRAGMA table_info(users)"))
            cols = [row[1] for row in result.fetchall()]
            if "must_change_password" not in cols:
                await conn.execute(text("ALTER TABLE users ADD COLUMN must_change_password BOOLEAN DEFAULT 0"))

            # 检查 email_accounts 表
            result = await conn.execute(text("PRAGMA table_info(email_accounts)"))
            cols = [row[1] for row in result.fetchall()]
            if "proxy_url" not in cols:
                await conn.execute(text("ALTER TABLE email_accounts ADD COLUMN proxy_url VARCHAR(255)"))
        except Exception:
            pass

    # 预置管理员账号
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.username == "admin"))
        admin_user = result.scalar_one_or_none()
        if not admin_user:
            admin_user = User(
                username="admin",
                email="admin@example.com",
                hashed_password=get_password_hash("admin123"),
                full_name="Administrator",
                is_active=True,
                is_superuser=True,
                # 首次登录强制修改密码
                must_change_password=True
            )
            session.add(admin_user)
            await session.commit()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    依赖注入用的数据库会话生成器
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def close_db():
    """关闭数据库连接"""
    await engine.dispose()


async def check_db_connection() -> bool:
    """检查数据库连接是否正常"""
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            result.scalar()
        return True
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"数据库连接检查失败: {e}")
        return False
