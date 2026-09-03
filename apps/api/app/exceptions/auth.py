from app.exceptions.base import AppError


class AdminLoginRejectedError(AppError):
    """Admin credentials, MFA setup, or TOTP verification failed."""


class AdminSessionError(AppError):
    """Admin bearer token missing, invalid, expired, or inactive admin."""


class PermissionDeniedError(AppError):
    """Authenticated admin lacks the required permission."""
