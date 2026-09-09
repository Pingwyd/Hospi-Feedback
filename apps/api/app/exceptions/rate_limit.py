from app.exceptions.base import AppError


class RateLimitExceededError(AppError):
    """Too many requests for this identifier in the current window."""
