"""
自定义异常模块
"""
from fastapi import HTTPException, status


class BaseAPIException(HTTPException):
    """基础 API 异常"""
    def __init__(
        self,
        status_code: int,
        detail: str,
        headers: dict = None
    ):
        super().__init__(
            status_code=status_code,
            detail=detail,
            headers=headers
        )


class AuthenticationError(BaseAPIException):
    """认证错误"""
    def __init__(self, detail: str = "认证失败"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )


class AuthorizationError(BaseAPIException):
    """授权错误"""
    def __init__(self, detail: str = "权限不足"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class NotFoundError(BaseAPIException):
    """资源不存在"""
    def __init__(self, detail: str = "资源不存在"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )


class ValidationError(BaseAPIException):
    """参数验证错误"""
    def __init__(self, detail: str = "参数验证失败"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail
        )


class ConflictError(BaseAPIException):
    """资源冲突"""
    def __init__(self, detail: str = "资源已存在"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail
        )


class RateLimitError(BaseAPIException):
    """请求频率限制"""
    def __init__(self, detail: str = "请求过于频繁"):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            headers={"Retry-After": "60"}
        )


class EmailServiceError(BaseAPIException):
    """邮件服务错误"""
    def __init__(self, detail: str = "邮件服务异常"):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=detail
        )


class IMAPError(EmailServiceError):
    """IMAP 连接错误"""
    def __init__(self, detail: str = "IMAP 连接失败"):
        super().__init__(detail=detail)


class OAuthError(EmailServiceError):
    """OAuth 认证错误"""
    def __init__(self, detail: str = "OAuth 认证失败"):
        super().__init__(detail=detail)