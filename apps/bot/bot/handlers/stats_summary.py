"""Shared aggregate summaries for /stats text and image captions."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from bot.handlers.stats_tokens import RESOLVED_STATUSES


def _coerce_status_counts(payload: dict[str, Any]) -> dict[str, int]:
    raw = payload.get("status_counts") or {}
    if not isinstance(raw, dict):
        return {}
    counts: dict[str, int] = {}
    for key, value in raw.items():
        try:
            counts[str(key)] = int(value)
        except (TypeError, ValueError):
            continue
    return counts


def _coerce_report_type_counts(payload: dict[str, Any]) -> dict[str, int]:
    raw = payload.get("report_type_counts") or {}
    if not isinstance(raw, dict):
        return {}
    counts: dict[str, int] = {}
    for key, value in raw.items():
        try:
            counts[str(key)] = int(value)
        except (TypeError, ValueError):
            continue
    return counts


def _coerce_submissions_by_day(payload: dict[str, Any]) -> list[dict[str, Any]]:
    raw = payload.get("submissions_by_day") or []
    if not isinstance(raw, list):
        return []
    return [item for item in raw if isinstance(item, dict)]


def summarize_status_mix(status_counts: dict[str, int]) -> dict[str, int]:
    total = sum(status_counts.values())
    unresolved = sum(
        count
        for status, count in status_counts.items()
        if status not in RESOLVED_STATUSES
    )
    resolved = sum(
        count for status, count in status_counts.items() if status in RESOLVED_STATUSES
    )
    escalated = status_counts.get("escalated", 0)
    return {
        "total": total,
        "unresolved": unresolved,
        "resolved": resolved,
        "escalated": escalated,
    }


def format_oldest_unresolved_line(entry: dict[str, Any] | None) -> str:
    if not entry:
        return "Oldest unresolved: none (backlog clear)."
    status = str(entry.get("status") or "unknown").replace("_", " ")
    created_at = str(entry.get("created_at") or "")
    if not created_at:
        return f"Oldest unresolved: status {status}."
    try:
        created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        age_days = max(0, (datetime.now(tz=UTC) - created.astimezone(UTC)).days)
        return f"Oldest unresolved: status {status}, open {age_days} day(s)."
    except ValueError:
        return f"Oldest unresolved: status {status}."


def submission_trend_total(
    submissions_by_day: list[dict[str, Any]], *, days: int = 7
) -> int:
    recent = submissions_by_day[-days:]
    return sum(int(item.get("count") or 0) for item in recent)


def format_stats_caption(payload: dict[str, Any]) -> str:
    """Compact caption for image mode (aggregate only, no report IDs)."""
    status_counts = _coerce_status_counts(payload)
    mix = summarize_status_mix(status_counts)
    submissions = _coerce_submissions_by_day(payload)
    oldest = payload.get("oldest_unresolved")
    trend_total = submission_trend_total(submissions, days=7)
    alerts = payload.get("system_alerts") or []

    lines = [
        "Hospi dashboard summary",
        (
            f"Reports: {mix['total']} total | {mix['unresolved']} unresolved | "
            f"{mix['escalated']} escalated"
        ),
        f"Last 7 days: {trend_total} submission(s)",
        format_oldest_unresolved_line(oldest if isinstance(oldest, dict) else None),
    ]
    if isinstance(alerts, list) and alerts:
        first = alerts[0]
        if isinstance(first, dict) and first.get("message"):
            lines.append(f"Alert: {first['message']}")
    caption = "\n".join(lines)
    return caption[:1024]
