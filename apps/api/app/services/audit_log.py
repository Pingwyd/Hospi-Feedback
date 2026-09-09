"""Shared audit_log writer for admin mutations."""

from __future__ import annotations

from typing import Any, Literal

from app.core.settings import Settings
from app.integrations.audit_log_store import insert_audit_log_row

AuditAction = Literal[
    "viewed",
    "status_changed",
    "assigned",
    "message_sent",
    "note_added",
    "exported",
    "escalated",
    "closed",
    "marked_false",
    "deleted",
    "other",
]


def write_audit_log(
    *,
    settings: Settings,
    admin_id: str,
    report_id: str | None,
    action: AuditAction,
    detail: dict[str, Any] | None = None,
) -> str:
    row = insert_audit_log_row(
        supabase_url=settings.supabase_url,
        service_role_key=settings.supabase_service_role_key,
        admin_id=admin_id,
        report_id=report_id,
        action=action,
        detail=detail,
    )
    return str(row["id"])
