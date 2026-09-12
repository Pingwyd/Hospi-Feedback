"""Business logic for anonymous reporter report lifecycle."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date
from typing import Any, Literal

from app.core.image_upload import prepare_image_for_storage
from app.core.settings import Settings
from app.core.ticket_code import (
    generate_ticket_code,
    hash_ticket_code,
    is_valid_ticket_code_format,
)
from app.exceptions.reports import (
    ReportClosedError,
    ReportNotFoundError,
)
from app.integrations.reports_store import (
    count_attachments_for_report,
    fetch_attachments_for_report,
    fetch_messages_for_report,
    fetch_report_by_ticket_hash,
    insert_attachment,
    insert_followup_attachment_atomic,
    insert_report,
    insert_report_categories,
    insert_reporter_message,
)
from app.integrations.supabase_storage import delete_object, upload_object
from app.services.attachment_delivery import (
    build_ticket_attachment_views,
    reporter_attachment_preview_path,
)

ReportType = Literal["complaint", "suggestion", "recognition"]
ReportSource = Literal["web", "telegram"]
Severity = Literal["low", "medium", "high"]
ReporterLockedStatus = frozenset({"closed"})
FOLLOWUP_PHOTO_MESSAGE = "Photo attached"


@dataclass(frozen=True)
class CreateReportInput:
    report_type: ReportType
    description: str
    source: ReportSource = "web"
    reported_member_name: str | None = None
    severity: Severity | None = None
    incident_date: date | None = None
    incident_location: str | None = None
    category_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class CreateReportResult:
    report_id: str
    ticket_code: str
    status: str
    created_at: str


def _store_kwargs(settings: Settings) -> dict[str, str]:
    return {
        "supabase_url": settings.supabase_url,
        "service_role_key": settings.supabase_service_role_key,
    }


def create_report(
    input_data: CreateReportInput, *, settings: Settings
) -> CreateReportResult:
    ticket_code = generate_ticket_code()
    row: dict[str, Any] = {
        "ticket_code_hash": hash_ticket_code(ticket_code),
        "source": input_data.source,
        "report_type": input_data.report_type,
        "description": input_data.description,
        "status": "new",
    }
    if input_data.reported_member_name is not None:
        row["reported_member_name"] = input_data.reported_member_name
    if input_data.severity is not None:
        row["severity"] = input_data.severity
    if input_data.incident_date is not None:
        row["incident_date"] = input_data.incident_date.isoformat()
    if input_data.incident_location is not None:
        row["incident_location"] = input_data.incident_location

    inserted = insert_report(**_store_kwargs(settings), row=row)
    report_id = str(inserted["id"])
    if input_data.category_ids:
        insert_report_categories(
            **_store_kwargs(settings),
            report_id=report_id,
            category_ids=list(input_data.category_ids),
        )
    return CreateReportResult(
        report_id=report_id,
        ticket_code=ticket_code,
        status=str(inserted.get("status") or "new"),
        created_at=str(inserted["created_at"]),
    )


def _load_report_by_ticket_code(
    ticket_code: str, *, settings: Settings
) -> dict[str, Any]:
    if not is_valid_ticket_code_format(ticket_code):
        raise ReportNotFoundError("Report not found.")
    report = fetch_report_by_ticket_hash(
        **_store_kwargs(settings),
        ticket_code_hash=hash_ticket_code(ticket_code),
    )
    if report is None:
        raise ReportNotFoundError("Report not found.")
    return report


def get_ticket_status(ticket_code: str, *, settings: Settings) -> dict[str, Any]:
    report = _load_report_by_ticket_code(ticket_code, settings=settings)
    store = _store_kwargs(settings)
    report_id = str(report["id"])
    messages = fetch_messages_for_report(**store, report_id=report_id)
    attachments = fetch_attachments_for_report(**store, report_id=report_id)
    report_level, by_message_id = build_ticket_attachment_views(
        ticket_code=ticket_code,
        attachments=attachments,
    )
    serialized_messages: list[dict[str, Any]] = []
    for message in messages:
        message_id = str(message["id"])
        entry: dict[str, Any] = {
            "id": message_id,
            "sender_type": message["sender_type"],
            "content": message["content"],
            "created_at": message["created_at"],
        }
        linked = by_message_id.get(message_id)
        if linked is not None:
            entry["attachment"] = linked
        serialized_messages.append(entry)
    return {
        "status": report["status"],
        "report_type": report["report_type"],
        "description": report["description"],
        "reported_member_name": report.get("reported_member_name"),
        "severity": report.get("severity"),
        "created_at": report["created_at"],
        "updated_at": report["updated_at"],
        "report_attachments": report_level,
        "messages": serialized_messages,
    }


def post_reporter_message(
    ticket_code: str,
    content: str,
    *,
    settings: Settings,
) -> dict[str, Any]:
    report = _load_report_by_ticket_code(ticket_code, settings=settings)
    if str(report.get("status") or "") in ReporterLockedStatus:
        raise ReportClosedError("Report is closed.")
    message = insert_reporter_message(
        **_store_kwargs(settings),
        report_id=str(report["id"]),
        content=content,
    )
    return {
        "report_id": str(report["id"]),
        "id": str(message["id"]),
        "sender_type": message["sender_type"],
        "content": message["content"],
        "created_at": message["created_at"],
    }


def upload_report_attachment(
    ticket_code: str,
    file_bytes: bytes,
    *,
    settings: Settings,
    link_to_thread: bool = False,
) -> dict[str, Any]:
    report = _load_report_by_ticket_code(ticket_code, settings=settings)
    if str(report.get("status") or "") in ReporterLockedStatus:
        raise ReportClosedError("Report is closed.")
    stripped, mime, extension = prepare_image_for_storage(
        file_bytes,
        max_bytes=settings.report_attachment_max_bytes,
    )
    attachment_id = str(uuid.uuid4())
    report_id = str(report["id"])
    storage_path = f"{report_id}/{attachment_id}.{extension}"
    upload_object(
        supabase_url=settings.supabase_url,
        service_role_key=settings.supabase_service_role_key,
        bucket=settings.report_attachments_bucket,
        object_path=storage_path,
        content=stripped,
        content_type=mime,
    )
    store = _store_kwargs(settings)
    try:
        if link_to_thread:
            row = insert_followup_attachment_atomic(
                **store,
                report_id=report_id,
                content=FOLLOWUP_PHOTO_MESSAGE,
                storage_path=storage_path,
                file_type=mime,
            )
            message_id = str(row["message_id"])
            attachment_row_id = str(row["attachment_id"])
            uploaded_at = str(row["attachment_uploaded_at"])
            preview_url = reporter_attachment_preview_path(
                ticket_code,
                attachment_row_id,
            )
            return {
                "report_id": report_id,
                "id": attachment_row_id,
                "file_type": str(row.get("file_type") or mime),
                "uploaded_at": uploaded_at,
                "message_id": message_id,
                "preview_url": preview_url,
            }
        attachment = insert_attachment(
            **store,
            report_id=report_id,
            storage_path=storage_path,
            file_type=mime,
        )
        attachment_row_id = str(attachment["id"])
        return {
            "report_id": report_id,
            "id": attachment_row_id,
            "file_type": str(attachment.get("file_type") or mime),
            "uploaded_at": attachment["uploaded_at"],
            "message_id": None,
            "preview_url": reporter_attachment_preview_path(
                ticket_code,
                attachment_row_id,
            ),
        }
    except Exception:
        delete_object(
            supabase_url=settings.supabase_url,
            service_role_key=settings.supabase_service_role_key,
            bucket=settings.report_attachments_bucket,
            object_path=storage_path,
        )
        raise


def count_report_attachments(report_id: str, *, settings: Settings) -> int:
    return count_attachments_for_report(
        **_store_kwargs(settings),
        report_id=report_id,
    )
