from app.exceptions.base import AppError


class AccessDeniedError(AppError):
    """Access-code session missing, invalid, or expired."""


class AccessCodeRejectedError(AppError):
    """Submitted access code did not match the configured value."""
