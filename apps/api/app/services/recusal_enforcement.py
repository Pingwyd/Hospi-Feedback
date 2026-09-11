"""Recusal enforcement for admin report mutations (spec section 9)."""

from __future__ import annotations

from app.core.admin_auth import AdminContext
from app.core.recusal import RecusalAdmin, RecusalReport, check_recusal
from app.core.settings import Settings
from app.exceptions.admin_reports import (
    RecusalBlockedError,
    RecusalConfirmationRequiredError,
)
from app.services.audit_log import write_audit_log

RECUSAL_SENSITIVE_STATUSES = frozenset({"closed", "marked_false"})


def recusal_report_from_row(report: dict) -> RecusalReport:
    linked = report.get("reported_member_admin_id")
    return RecusalReport(
        reported_member_name=report.get("reported_member_name"),
        reported_member_admin_id=str(linked) if linked else None,
    )


def recusal_admin_from_context(admin: AdminContext) -> RecusalAdmin:
    return RecusalAdmin(
        id=admin.id,
        full_name=admin.full_name,
        aliases=admin.aliases,
    )


def enforce_recusal_for_mutation(
    *,
    admin: AdminContext,
    report: dict,
    confirm_recusal_override: bool,
    settings: Settings,
) -> None:
    """Run Phase 2 check_recusal and write warn/block audit rows when needed."""
    result = check_recusal(
        recusal_admin_from_context(admin),
        recusal_report_from_row(report),
    )
    report_id = str(report["id"])
    if result == "clear":
        return
    if result == "blocked":
        write_audit_log(
            settings=settings,
            admin_id=admin.id,
            report_id=report_id,
            action="other",
            detail={"event": "recusal_blocked"},
        )
        raise RecusalBlockedError(
            "You cannot act on this report because you are named on it."
        )
    if not confirm_recusal_override:
        write_audit_log(
            settings=settings,
            admin_id=admin.id,
            report_id=report_id,
            action="other",
            detail={"event": "recusal_warn", "confirmed": False},
        )
        raise RecusalConfirmationRequiredError(
            "This report may name you. Set confirm_recusal_override to proceed."
        )


def audit_action_for_status(status: str) -> str:
    if status == "marked_false":
        return "marked_false"
    if status == "closed":
        return "closed"
    return "status_changed"
