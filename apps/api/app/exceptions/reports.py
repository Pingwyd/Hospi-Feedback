from app.exceptions.base import AppError


class ReportNotFoundError(AppError):
    """Ticket code did not match any report."""


class ReportClosedError(AppError):
    """Reporter actions are not allowed on closed reports."""


class AttachmentRejectedError(AppError):
    """Uploaded file failed validation."""
