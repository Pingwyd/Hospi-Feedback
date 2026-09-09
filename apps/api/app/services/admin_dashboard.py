"""Dashboard stats aggregation for admin charts."""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Any

from app.core.admin_auth import AdminContext
from app.core.settings import Settings
from app.exceptions.auth import PermissionDeniedError
from app.integrations.reports_store import list_reports

RESOLVED_STATUSES = frozenset({"resolved", "closed", "marked_false"})


def _store_kwargs(settings: Settings) -> dict[str, str]:
    return {
        "supabase_url": settings.supabase_url,
        "service_role_key": settings.supabase_service_role_key,
    }


def _require_view(admin: AdminContext) -> None:
    if "view" not in admin.permissions:
        raise PermissionDeniedError(
            "Permission 'view' is required for this action.",
        )


def _day_key(created_at: str) -> str:
    return datetime.fromisoformat(created_at.replace("Z", "+00:00")).date().isoformat()


def get_dashboard_stats(*, admin: AdminContext, settings: Settings) -> dict[str, Any]:
    _require_view(admin)
    reports = list_reports(**_store_kwargs(settings), limit=1000, offset=0)
    status_counts: Counter[str] = Counter()
    report_type_counts: Counter[str] = Counter()
    submissions_by_day: Counter[str] = Counter()
    oldest_unresolved: dict[str, Any] | None = None

    for report in reports:
        status = str(report.get("status") or "unknown")
        status_counts[status] += 1
        report_type = str(report.get("report_type") or "unknown")
        report_type_counts[report_type] += 1
        created_at = str(report.get("created_at") or "")
        if created_at:
            submissions_by_day[_day_key(created_at)] += 1
        if status not in RESOLVED_STATUSES:
            if oldest_unresolved is None or created_at < str(
                oldest_unresolved.get("created_at") or ""
            ):
                oldest_unresolved = {
                    "report_id": report["id"],
                    "status": status,
                    "created_at": created_at,
                }

    return {
        "status_counts": dict(status_counts),
        "report_type_counts": dict(report_type_counts),
        "submissions_by_day": [
            {"date": day, "count": count}
            for day, count in sorted(submissions_by_day.items())
        ],
        "oldest_unresolved": oldest_unresolved,
    }
