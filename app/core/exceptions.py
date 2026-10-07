from typing import Any, Optional
from fastapi import HTTPException, status


class AppException(HTTPException):
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: str = "ERROR",
        extra: Optional[Any] = None
    ):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code
        self.extra = extra


class NotFoundException(AppException):
    def __init__(self, detail: str = "Resource not found", extra: Optional[Any] = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code="NOT_FOUND",
            extra=extra
        )


class UnauthorizedException(AppException):
    def __init__(self, detail: str = "Authentication required", extra: Optional[Any] = None):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="UNAUTHORIZED",
            extra=extra
        )


class ForbiddenException(AppException):
    def __init__(self, detail: str = "Permission denied", extra: Optional[Any] = None):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code="FORBIDDEN",
            extra=extra
        )


class BadRequestException(AppException):
    def __init__(self, detail: str = "Bad request", extra: Optional[Any] = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code="BAD_REQUEST",
            extra=extra
        )


class ConflictException(AppException):
    def __init__(self, detail: str = "Resource conflict", extra: Optional[Any] = None):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            error_code="CONFLICT",
            extra=extra
        )
