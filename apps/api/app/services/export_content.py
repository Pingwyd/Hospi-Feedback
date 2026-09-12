"""Shared field selection for filtered on-demand admin exports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True)
class ExportFilters:
    status: str | None
    keyword: str | None
    created_from: str | None
    created_to: str | None

    def as_detail_dict(self) -> dict[str, str | None]:
        return {
            "status": self.status,
            "keyword": self.keyword,
            "created_from": self.created_from,
            "created_to": self.created_to,
        }


@dataclass(frozen=True)
class ExportReportEntry:
    id: str
    report_type: str
    status: str
    severity: str
    incident_date: str | None
    incident_location: str | None
    description: str
    reported_member_name: str | None
    created_at: str
    updated_at: str
    categories: tuple[str, ...]


@dataclass(frozen=True)
class FilteredExportDocument:
    exported_at: str
    filters: ExportFilters
    report_count: int
    truncated: bool
    export_limit: int
    reports: tuple[ExportReportEntry, ...]


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def report_entry_from_row(
    row: dict[str, Any],
    *,
    categories: list[str] | None = None,
) -> ExportReportEntry:
    """Map a reports row to export-safe fields only."""
    return ExportReportEntry(
        id=str(row.get("id") or ""),
        report_type=str(row.get("report_type") or "N/A"),
        status=str(row.get("status") or "unknown"),
        severity=str(row.get("severity") or "N/A"),
        incident_date=_optional_text(row.get("incident_date")),
        incident_location=_optional_text(row.get("incident_location")),
        description=str(row.get("description") or ""),
        reported_member_name=_optional_text(row.get("reported_member_name")),
        created_at=str(row.get("created_at") or "N/A"),
        updated_at=str(row.get("updated_at") or "N/A"),
        categories=tuple(categories or ()),
    )


def assemble_filtered_export_document(
    *,
    rows: list[dict[str, Any]],
    category_names_by_report: dict[str, list[str]],
    filters: ExportFilters,
    export_limit: int,
) -> FilteredExportDocument:
    exported_at = datetime.now(tz=UTC).isoformat().replace("+00:00", "Z")
    entries = [
        report_entry_from_row(
            row,
            categories=category_names_by_report.get(str(row.get("id") or ""), []),
        )
        for row in rows
    ]
    truncated = len(rows) >= export_limit
    return FilteredExportDocument(
        exported_at=exported_at,
        filters=filters,
        report_count=len(entries),
        truncated=truncated,
        export_limit=export_limit,
        reports=tuple(entries),
    )


def filters_summary_label(filters: ExportFilters) -> str:
    parts: list[str] = []
    if filters.status:
        parts.append(f"status-{filters.status}")
    if filters.keyword:
        parts.append("keyword")
    if filters.created_from or filters.created_to:
        parts.append("date-range")
    if not parts:
        return "all"
    return "-".join(parts)


def export_filename(*, filters: ExportFilters, export_format: str) -> str:
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    suffix = "docx" if export_format == "docx" else "pdf"
    return f"hospi-export-{filters_summary_label(filters)}-{stamp}.{suffix}"
