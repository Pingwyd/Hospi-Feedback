"""Admin report triage business logic."""

from __future__ import annotations

from typing import Any

from app.core.admin_auth import AdminContext
from app.core.settings import Settings
from app.exceptions.admin_reports import (
    AdminReportValidationError,
    HohRoleRequiredError,
)
from app.exceptions.reports import ReportNotFoundError
from app.integrations.reports_store import (
    fetch_internal_notes_for_report,
    fetch_messages_for_report,
    fetch_report_by_id,
    insert_admin_message,
    insert_escalation,
    insert_internal_note,
    list_reports,
    patch_report_fields,
)
from app.services.admin_ws import broadcast_admin_event
from app.services.audit_log import AuditAction, write_audit_log
from app.services.recusal_enforcement import (
    RECUSAL_SENSITIVE_STATUSES,
    audit_action_for_status,
    enforce_recusal_for_mutation,
)
from app.services.report_archive import archive_report


def _store_kwargs(settings: Settings) -> dict[str, str]:
    return {
        "supabase_url": settings.supabase_url,
        "service_role_key": settings.supabase_service_role_key,
    }


def _load_report_or_raise(report_id: str, *, settings: Settings) -> dict[str, Any]:
    report = fetch_report_by_id(**_store_kwargs(settings), report_id=report_id)
    if report is None:
        raise ReportNotFoundError("Report not found.")
    return report


def _permission_for_status(status: str) -> str:
    if status in RECUSAL_SENSITIVE_STATUSES or status == "resolved":
        return "close"
    if status == "assigned":
        return "assign"
    return "respond"


def _require_permission(admin: AdminContext, permission: str) -> None:
    from app.exceptions.auth import PermissionDeniedError

    if permission not in admin.permissions:
        raise PermissionDeniedError(
            f"Permission '{permission}' is required for this action.",
        )


def list_admin_reports(
    *,
    admin: AdminContext,
    settings: Settings,
    status: str | None = None,
    keyword: str | None = None,
    created_from: str | None = None,
    created_to: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict[str, Any]]:
    _require_permission(admin, "view")
    return list_reports(
        **_store_kwargs(settings),
        status=status,
        keyword=keyword,
        created_from=created_from,
        created_to=created_to,
        limit=limit,
        offset=offset,
    )


def get_admin_report(
    *,
    report_id: str,
    admin: AdminContext,
    settings: Settings,
) -> dict[str, Any]:
    _require_permission(admin, "view")
    report = _load_report_or_raise(report_id, settings=settings)
    store = _store_kwargs(settings)
    return {
        "report": report,
        "messages": fetch_messages_for_report(**store, report_id=report_id),
        "internal_notes": fetch_internal_notes_for_report(**store, report_id=report_id),
    }


def apply_report_status_change(
    *,
    report_id: str,
    new_status: str,
    admin: AdminContext,
    settings: Settings,
    confirm_recusal_override: bool = False,
) -> dict[str, Any]:
    _require_permission(admin, _permission_for_status(new_status))
    report = _load_report_or_raise(report_id, settings=settings)
    if new_status in RECUSAL_SENSITIVE_STATUSES:
        enforce_recusal_for_mutation(
            admin=admin,
            report=report,
            confirm_recusal_override=confirm_recusal_override,
            settings=settings,
        )
    previous_status = report.get("status")
    updated = patch_report_fields(
        **_store_kwargs(settings),
        report_id=report_id,
        fields={"status": new_status},
    )
    detail: dict[str, Any] = {
        "from_status": previous_status,
        "to_status": new_status,
    }
    if confirm_recusal_override:
        detail["recusal_override"] = True
    action: AuditAction = audit_action_for_status(new_status)  # type: ignore[assignment]
    write_audit_log(
        settings=settings,
        admin_id=admin.id,
        report_id=report_id,
        action=action,
        detail=detail,
    )
    return updated


def mark_report_false(
    *,
    report_id: str,
    admin: AdminContext,
    settings: Settings,
    confirm_recusal_override: bool = False,
) -> dict[str, Any]:
    return apply_report_status_change(
        report_id=report_id,
        new_status="marked_false",
        admin=admin,
        settings=settings,
        confirm_recusal_override=confirm_recusal_override,
    )


def assign_report(
    *,
    report_id: str,
    assigned_admin_id: str,
    admin: AdminContext,
    settings: Settings,
) -> dict[str, Any]:
    _require_permission(admin, "assign")
    _load_report_or_raise(report_id, settings=settings)
    updated = patch_report_fields(
        **_store_kwargs(settings),
        report_id=report_id,
        fields={
            "assigned_admin_id": assigned_admin_id,
            "status": "assigned",
        },
    )
    write_audit_log(
        settings=settings,
        admin_id=admin.id,
        report_id=report_id,
        action="assigned",
        detail={"assigned_admin_id": assigned_admin_id},
    )
    return updated


def link_report_member(
    *,
    report_id: str,
    reported_member_admin_id: str,
    admin: AdminContext,
    settings: Settings,
) -> dict[str, Any]:
    _require_permission(admin, "assign")
    _load_report_or_raise(report_id, settings=settings)
    updated = patch_report_fields(
        **_store_kwargs(settings),
        report_id=report_id,
        fields={"reported_member_admin_id": reported_member_admin_id},
    )
    write_audit_log(
        settings=settings,
        admin_id=admin.id,
        report_id=report_id,
        action="other",
        detail={
            "event": "link_member",
            "reported_member_admin_id": reported_member_admin_id,
        },
    )
    return updated


def add_internal_note(
    *,
    report_id: str,
    content: str,
    admin: AdminContext,
    settings: Settings,
) -> dict[str, Any]:
    _require_permission(admin, "respond")
    _load_report_or_raise(report_id, settings=settings)
    note = insert_internal_note(
        **_store_kwargs(settings),
        report_id=report_id,
        admin_id=admin.id,
        content=content,
    )
    write_audit_log(
        settings=settings,
        admin_id=admin.id,
        report_id=report_id,
        action="note_added",
        detail={"note_id": note["id"]},
    )
    return note


def send_reporter_message(
    *,
    report_id: str,
    content: str,
    admin: AdminContext,
    settings: Settings,
) -> dict[str, Any]:
    _require_permission(admin, "respond")
    report = _load_report_or_raise(report_id, settings=settings)
    if report.get("status") == "closed":
        from app.exceptions.reports import ReportClosedError

        raise ReportClosedError("Report is closed.")
    message = insert_admin_message(
        **_store_kwargs(settings),
        report_id=report_id,
        sender_admin_id=admin.id,
        content=content,
    )
    write_audit_log(
        settings=settings,
        admin_id=admin.id,
        report_id=report_id,
        action="message_sent",
        detail={"message_id": message["id"]},
    )
    return message


async def send_reporter_message_and_notify(
    *,
    report_id: str,
    content: str,
    admin: AdminContext,
    settings: Settings,
) -> dict[str, Any]:
    message = send_reporter_message(
        report_id=report_id,
        content=content,
        admin=admin,
        settings=settings,
    )
    await broadcast_admin_event(
        "new_message",
        {
            "report_id": report_id,
            "message_id": message["id"],
            "sender_type": "admin",
            "created_at": message["created_at"],
        },
    )
    return message


def escalate_report(
    *,
    report_id: str,
    escalation_contact_id: str,
    admin: AdminContext,
    settings: Settings,
) -> dict[str, Any]:
    _require_permission(admin, "respond")
    _load_report_or_raise(report_id, settings=settings)
    escalation = insert_escalation(
        **_store_kwargs(settings),
        report_id=report_id,
        escalation_contact_id=escalation_contact_id,
        escalated_by_admin_id=admin.id,
    )
    updated = patch_report_fields(
        **_store_kwargs(settings),
        report_id=report_id,
        fields={"status": "escalated"},
    )
    write_audit_log(
        settings=settings,
        admin_id=admin.id,
        report_id=report_id,
        action="escalated",
        detail={
            "escalation_id": escalation["id"],
            "escalation_contact_id": escalation_contact_id,
        },
    )
    return {"report": updated, "escalation": escalation}


def delete_report_by_hoh(
    *,
    report_id: str,
    delete_reason: str,
    admin: AdminContext,
    settings: Settings,
) -> None:
    """Audit first, then archive. Route layer owns the deleted audit row."""
    if admin.role != "hoh":
        raise HohRoleRequiredError("Only the Head of Hospi may delete reports.")
    reason = delete_reason.strip()
    if not reason:
        raise AdminReportValidationError("delete_reason is required.")
    _load_report_or_raise(report_id, settings=settings)
    write_audit_log(
        settings=settings,
        admin_id=admin.id,
        report_id=report_id,
        action="deleted",
        detail={"delete_reason": reason},
    )
    archive_report(
        report_id=report_id,
        archive_reason="admin_deleted",
        settings=settings,
        deleted_by_admin_id=admin.id,
        delete_reason=reason,
    )
