"""Unified report archive path for admin delete and scheduled purge (Phase 5)."""

from __future__ import annotations

from typing import Any, Literal

from app.core.settings import Settings
from app.exceptions.reports import ReportNotFoundError
from app.integrations.report_archive_store import (
    delete_report_row,
    delete_rows_for_report,
    insert_archived_report,
)
from app.integrations.reports_store import (
    fetch_category_names_for_report,
    fetch_report_by_id,
)

ArchiveReason = Literal["scheduled_purge", "admin_deleted"]

_CHILD_TABLES = (
    "messages",
    "internal_notes",
    "attachments",
    "report_categories",
)


def _store_kwargs(settings: Settings) -> dict[str, str]:
    return {
        "supabase_url": settings.supabase_url,
        "service_role_key": settings.supabase_service_role_key,
    }


def _status_history_snapshot(report: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "status": report.get("status"),
            "updated_at": report.get("updated_at"),
        }
    ]


def archive_report(
    *,
    report_id: str,
    archive_reason: ArchiveReason,
    settings: Settings,
    deleted_by_admin_id: str | None = None,
    delete_reason: str | None = None,
) -> str:
    """Archive metadata and remove live report rows. Audit-agnostic by design."""
    store = _store_kwargs(settings)
    report = fetch_report_by_id(**store, report_id=report_id)
    if report is None:
        raise ReportNotFoundError("Report not found.")

    if archive_reason == "admin_deleted":
        if not deleted_by_admin_id or not (delete_reason or "").strip():
            raise ValueError(
                "Admin delete requires deleted_by_admin_id and delete_reason."
            )

    categories = fetch_category_names_for_report(**store, report_id=report_id)
    handled_by = report.get("assigned_admin_id") or report.get(
        "reported_member_admin_id"
    )
    archived_row = insert_archived_report(
        **store,
        row={
            "original_report_id": report_id,
            "ticket_code_hash": report.get("ticket_code_hash"),
            "categories": categories,
            "status_history": _status_history_snapshot(report),
            "resolution_summary": None,
            "handled_by_admin_id": handled_by,
            "archive_reason": archive_reason,
            "deleted_by_admin_id": deleted_by_admin_id,
            "delete_reason": delete_reason,
            "created_at": report.get("created_at"),
        },
    )

    for table in _CHILD_TABLES:
        delete_rows_for_report(**store, table=table, report_id=report_id)
    delete_report_row(**store, report_id=report_id)
    return str(archived_row["id"])
