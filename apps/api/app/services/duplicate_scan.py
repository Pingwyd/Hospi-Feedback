"""Flag possibly related reports based on member name, category, and time window."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from app.core.settings import Settings
from app.integrations.internal_jobs_store import (
    fetch_category_ids_for_reports,
    list_reports_for_duplicate_scan,
)
from app.integrations.reports_store import patch_report_fields


def _store_kwargs(settings: Settings) -> dict[str, str]:
    return {
        "supabase_url": settings.supabase_url,
        "service_role_key": settings.supabase_service_role_key,
    }


def _normalize_member_name(value: object) -> str:
    return str(value or "").strip().casefold()


def _parse_created_at(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def run_duplicate_scan(*, settings: Settings) -> dict[str, Any]:
    """Soft-flag younger reports that may duplicate an earlier report."""
    reports = list_reports_for_duplicate_scan(**_store_kwargs(settings))
    if not reports:
        return {"flagged_count": 0, "flagged_pairs": []}

    report_ids = [str(report["id"]) for report in reports]
    category_map = fetch_category_ids_for_reports(
        **_store_kwargs(settings),
        report_ids=report_ids,
    )
    window = timedelta(days=settings.duplicate_scan_window_days)
    flagged_pairs: list[dict[str, str]] = []

    for index, report in enumerate(reports):
        report_id = str(report["id"])
        member = _normalize_member_name(report.get("reported_member_name"))
        if not member:
            continue
        created_at = _parse_created_at(report.get("created_at"))
        if created_at is None:
            continue
        categories = category_map.get(report_id, set())
        if not categories:
            continue

        for earlier in reports[:index]:
            earlier_id = str(earlier["id"])
            if _normalize_member_name(earlier.get("reported_member_name")) != member:
                continue
            earlier_created = _parse_created_at(earlier.get("created_at"))
            if earlier_created is None:
                continue
            if created_at - earlier_created > window:
                continue
            earlier_categories = category_map.get(earlier_id, set())
            if not categories.intersection(earlier_categories):
                continue
            patch_report_fields(
                **_store_kwargs(settings),
                report_id=report_id,
                fields={"possible_duplicate_of": earlier_id},
            )
            flagged_pairs.append(
                {"report_id": report_id, "possible_duplicate_of": earlier_id}
            )
            break

    return {"flagged_count": len(flagged_pairs), "flagged_pairs": flagged_pairs}
