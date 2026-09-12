"""Structured text formatting for /stats (text render mode)."""

from __future__ import annotations

from typing import Any

from bot.handlers.stats_summary import (
    _coerce_report_type_counts,
    _coerce_status_counts,
    _coerce_submissions_by_day,
    format_oldest_unresolved_line,
    submission_trend_total,
    summarize_status_mix,
)


def _format_status_counts(status_counts: dict[str, int]) -> list[str]:
    if not status_counts:
        return ["No reports in the current window."]
    lines: list[str] = []
    for status, count in sorted(
        status_counts.items(),
        key=lambda item: (-item[1], item[0]),
    ):
        label = status.replace("_", " ")
        lines.append(f"- {label}: {count}")
    return lines


def _format_report_type_counts(report_type_counts: dict[str, int]) -> list[str]:
    if not report_type_counts:
        return []
    lines: list[str] = []
    for report_type, count in sorted(
        report_type_counts.items(),
        key=lambda item: (-item[1], item[0]),
    ):
        lines.append(f"- {report_type.replace('_', ' ')}: {count}")
    return lines


def _format_submission_trend(submissions_by_day: list[dict[str, Any]]) -> list[str]:
    if not submissions_by_day:
        return ["Submission trend: no submissions recorded yet."]
    recent = submissions_by_day[-7:]
    total = submission_trend_total(submissions_by_day, days=7)
    lines = [f"Submission trend (last {len(recent)} day(s)): {total} total"]
    for item in recent:
        day = str(item.get("date") or "unknown")
        count = int(item.get("count") or 0)
        lines.append(f"- {day}: {count}")
    return lines


def format_dashboard_stats_text(payload: dict[str, Any]) -> str:
    """Render aggregate dashboard stats as Telegram-safe plain text."""
    status_counts = _coerce_status_counts(payload)
    report_type_counts = _coerce_report_type_counts(payload)
    submissions_by_day = _coerce_submissions_by_day(payload)
    oldest_unresolved = payload.get("oldest_unresolved")
    system_alerts = payload.get("system_alerts") or []
    mix = summarize_status_mix(status_counts)

    lines = [
        "Hospi dashboard summary",
        "",
        (
            f"Overview: {mix['total']} total | {mix['unresolved']} unresolved | "
            f"{mix['resolved']} resolved | {mix['escalated']} escalated"
        ),
        "",
        "Status breakdown:",
        *_format_status_counts(status_counts),
    ]

    type_lines = _format_report_type_counts(report_type_counts)
    if type_lines:
        lines.extend(["", "Report types:", *type_lines])

    lines.extend(
        [
            "",
            format_oldest_unresolved_line(
                oldest_unresolved if isinstance(oldest_unresolved, dict) else None
            ),
            "",
            *_format_submission_trend(submissions_by_day),
        ]
    )

    if isinstance(system_alerts, list) and system_alerts:
        lines.extend(["", f"System alerts: {len(system_alerts)} active"])
        first = system_alerts[0]
        if isinstance(first, dict) and first.get("message"):
            lines.append(f"- {first['message']}")

    text = "\n".join(lines)
    if len(text) > 4000:
        return text[:3997] + "..."
    return text
