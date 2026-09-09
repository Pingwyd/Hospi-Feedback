from app.exceptions.base import AppError


class TelegramLinkRejectedError(AppError):
    """Link code invalid, expired, already used, or chat id rejected."""


class TelegramAdminNotLinkedError(AppError):
    """No active admin row matches the supplied Telegram chat id."""
