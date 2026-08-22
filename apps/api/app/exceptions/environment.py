from app.exceptions.base import AppError


class EnvironmentGuardError(AppError):
    """Operation is blocked for this ENVIRONMENT value."""
