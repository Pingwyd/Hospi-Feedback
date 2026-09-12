"""Ticket-scoped attachment proxy delivery for reporters and admins."""

from __future__ import annotations

from app.core.admin_auth import AdminContext
from app.core.settings import Settings
from app.core.ticket_code import hash_ticket_code, is_valid_ticket_code_format
from app.exceptions.auth import PermissionDeniedError
from app.exceptions.reports import ReportNotFoundError
from app.integrations.reports_store import (
    fetch_attachment_by_id,
    fetch_report_by_id,
    fetch_report_by_ticket_hash,
)
from app.integrations.supabase_storage import StorageDownloadError, download_object


def _store_kwargs(settings: Settings) -> dict[str, str]:
    return {
        "supabase_url": settings.supabase_url,
        "service_role_key": settings.supabase_service_role_key,
    }


def _download_attachment_bytes(
    *,
    attachment: dict,
    settings: Settings,
) -> tuple[bytes, str]:
    storage_path = str(attachment.get("storage_path") or "")
    if not storage_path:
        raise ReportNotFoundError("Attachment not found.")
    file_type = str(attachment.get("file_type") or "application/octet-stream")
    try:
        content, header_type = download_object(
            supabase_url=settings.supabase_url,
            service_role_key=settings.supabase_service_role_key,
            bucket=settings.report_attachments_bucket,
            object_path=storage_path,
        )
    except StorageDownloadError as exc:
        raise ReportNotFoundError("Attachment not found.") from exc
    content_type = header_type or file_type
    return content, content_type


def reporter_attachment_preview_path(ticket_code: str, attachment_id: str) -> str:
    return f"/api/reports/ticket/{ticket_code}/attachments/{attachment_id}"


def admin_attachment_preview_path(report_id: str, attachment_id: str) -> str:
    return f"/api/admin/reports/{report_id}/attachments/{attachment_id}"


def serialize_attachment_summary(
    *,
    attachment: dict,
    preview_path: str,
) -> dict[str, str]:
    return {
        "id": str(attachment["id"]),
        "file_type": str(attachment.get("file_type") or "application/octet-stream"),
        "uploaded_at": str(attachment["uploaded_at"]),
        "preview_url": preview_path,
    }


def build_ticket_attachment_views(
    *,
    ticket_code: str,
    attachments: list[dict],
) -> tuple[list[dict], dict[str, dict]]:
    """Return report-level attachments and a map message_id -> attachment summary."""
    report_level: list[dict] = []
    by_message_id: dict[str, dict] = {}
    for row in attachments:
        preview_path = reporter_attachment_preview_path(
            ticket_code,
            str(row["id"]),
        )
        summary = serialize_attachment_summary(
            attachment=row,
            preview_path=preview_path,
        )
        message_id = row.get("message_id")
        if message_id is None:
            report_level.append(summary)
        else:
            by_message_id[str(message_id)] = summary
    return report_level, by_message_id


def build_admin_attachment_views(
    *,
    report_id: str,
    attachments: list[dict],
) -> tuple[list[dict], dict[str, dict]]:
    report_level: list[dict] = []
    by_message_id: dict[str, dict] = {}
    for row in attachments:
        preview_path = admin_attachment_preview_path(report_id, str(row["id"]))
        summary = serialize_attachment_summary(
            attachment=row,
            preview_path=preview_path,
        )
        message_id = row.get("message_id")
        if message_id is None:
            report_level.append(summary)
        else:
            by_message_id[str(message_id)] = summary
    return report_level, by_message_id


def fetch_reporter_attachment_bytes(
    *,
    ticket_code: str,
    attachment_id: str,
    settings: Settings,
) -> tuple[bytes, str]:
    if not is_valid_ticket_code_format(ticket_code):
        raise ReportNotFoundError("Attachment not found.")
    report = fetch_report_by_ticket_hash(
        **_store_kwargs(settings),
        ticket_code_hash=hash_ticket_code(ticket_code),
    )
    if report is None:
        raise ReportNotFoundError("Attachment not found.")
    attachment = fetch_attachment_by_id(
        **_store_kwargs(settings),
        attachment_id=attachment_id,
    )
    if attachment is None or str(attachment.get("report_id")) != str(report["id"]):
        raise ReportNotFoundError("Attachment not found.")
    return _download_attachment_bytes(attachment=attachment, settings=settings)


def fetch_admin_attachment_bytes(
    *,
    report_id: str,
    attachment_id: str,
    admin: AdminContext,
    settings: Settings,
) -> tuple[bytes, str]:
    if "view" not in admin.permissions:
        raise PermissionDeniedError(
            "Permission 'view' is required for this action.",
        )
    report = fetch_report_by_id(**_store_kwargs(settings), report_id=report_id)
    if report is None:
        raise ReportNotFoundError("Attachment not found.")
    attachment = fetch_attachment_by_id(
        **_store_kwargs(settings),
        attachment_id=attachment_id,
    )
    if attachment is None or str(attachment.get("report_id")) != str(report_id):
        raise ReportNotFoundError("Attachment not found.")
    return _download_attachment_bytes(attachment=attachment, settings=settings)
