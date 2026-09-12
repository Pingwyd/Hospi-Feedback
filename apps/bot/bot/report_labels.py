"""User-facing labels for report types (distinct from API enum values)."""

from __future__ import annotations

REPORT_TYPE_LABELS: dict[str, str] = {
    "complaint": "Report Concern",
    "suggestion": "Suggest Something",
    "recognition": "Shoutout",
}


def report_type_label(report_type: str) -> str:
    return REPORT_TYPE_LABELS.get(report_type, report_type.replace("_", " "))
