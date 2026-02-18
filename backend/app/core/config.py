"""
配置管理模块
"""
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    # 基础配置
    debug: bool = Field(default=False, alias="DEBUG")
    app_name: str = Field(default="Mailbox Manager", alias="APP_NAME")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    
    # 数据库配置
    database_url: str = Field(
        default="sqlite+aiosqlite:///./data/mailbox_v2.db",
        alias="DATABASE_URL"
    )
    
    # 安全配置
    secret_key: str = Field(default="change-me-in-production", alias="SECRET_KEY")
    access_token_expire_minutes: int = Field(default=1440, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, alias="REFRESH_TOKEN_EXPIRE_DAYS")
    algorithm: str = Field(default="HS256", alias="ALGORITHM")
    
    # Microsoft OAuth 配置
    microsoft_client_id: Optional[str] = Field(default=None, alias="MICROSOFT_CLIENT_ID")
    microsoft_client_secret: Optional[str] = Field(default=None, alias="MICROSOFT_CLIENT_SECRET")
    microsoft_redirect_uri: str = Field(
        default="http://localhost:8000/api/v1/auth/microsoft/callback",
        alias="MICROSOFT_REDIRECT_URI"
    )
    
    # Google OAuth 配置
    google_client_id: Optional[str] = Field(default=None, alias="GOOGLE_CLIENT_ID")
    google_client_secret: Optional[str] = Field(default=None, alias="GOOGLE_CLIENT_SECRET")
    google_redirect_uri: str = Field(
        default="http://localhost:8000/api/v1/auth/google/callback",
        alias="GOOGLE_REDIRECT_URI"
    )
    
    # IMAP 配置
    imap_timeout: int = Field(default=30, alias="IMAP_TIMEOUT")
    imap_max_connections: int = Field(default=10, alias="IMAP_MAX_CONNECTIONS")
    
    # Redis 配置（可选）
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    redis_enabled: bool = Field(default=False, alias="REDIS_ENABLED")
    
    # 邮件处理配置
    max_email_size: str = Field(default="50MB", alias="MAX_EMAIL_SIZE")
    email_batch_size: int = Field(default=50, alias="EMAIL_BATCH_SIZE")
    fetch_interval_minutes: int = Field(default=5, alias="FETCH_INTERVAL_MINUTES")
    
    # 日志配置
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: str = Field(default="json", alias="LOG_FORMAT")
    
    @property
    def async_database_url(self) -> str:
        """获取异步数据库URL"""
        url = self.database_url
        if url.startswith("sqlite://") and "aiosqlite" not in url:
            url = url.replace("sqlite://", "sqlite+aiosqlite://")
        return url
    
    @property
    def is_production(self) -> bool:
        """判断是否为生产环境"""
        return not self.debug


# 全局配置实例
settings = Settings()