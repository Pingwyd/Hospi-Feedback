"""Filtered on-demand admin report export."""

from __future__ import annotations

from typing import Literal

from app.core.admin_auth import AdminContext
from app.core.docx_builder import build_filtered_export_docx
from app.core.pdf_builder import build_filtered_export_pdf
from app.core.settings import Settings
from app.exceptions.auth import PermissionDeniedError
from app.integrations.reports_store import (
    fetch_category_names_for_reports,
    list_reports,
)
from app.services.audit_log import write_audit_log
from app.services.export_content import (
    ExportFilters,
    assemble_filtered_export_document,
    export_filename,
)

EXPORT_REPORT_LIMIT = 200

ExportFormat = Literal["pdf", "docx"]

_MEDIA_TYPES: dict[ExportFormat, str] = {
    "pdf": "application/pdf",
    "docx": ("application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
}


def _store_kwargs(settings: Settings) -> dict[str, str]:
    return {
        "supabase_url": settings.supabase_url,
        "service_role_key": settings.supabase_service_role_key,
    }


def _require_export_permission(admin: AdminContext) -> None:
    if "export" not in admin.permissions:
        raise PermissionDeniedError(
            "Permission 'export' is required for this action.",
        )


def build_filtered_admin_export(
    *,
    admin: AdminContext,
    settings: Settings,
    export_format: ExportFormat,
    status: str | None = None,
    keyword: str | None = None,
    created_from: str | None = None,
    created_to: str | None = None,
) -> tuple[bytes, str, str]:
    """Return document bytes, filename, and media type."""
    _require_export_permission(admin)
    filters = ExportFilters(
        status=status,
        keyword=keyword,
        created_from=created_from,
        created_to=created_to,
    )
    store = _store_kwargs(settings)
    rows = list_reports(
        **store,
        status=status,
        keyword=keyword,
        created_from=created_from,
        created_to=created_to,
        limit=EXPORT_REPORT_LIMIT,
        offset=0,
    )
    report_ids = [str(row.get("id") or "") for row in rows if row.get("id")]
    category_names = (
        fetch_category_names_for_reports(**store, report_ids=report_ids)
        if report_ids
        else {}
    )
    document = assemble_filtered_export_document(
        rows=rows,
        category_names_by_report=category_names,
        filters=filters,
        export_limit=EXPORT_REPORT_LIMIT,
    )
    if export_format == "docx":
        content = build_filtered_export_docx(document)
    else:
        content = build_filtered_export_pdf(document)

    write_audit_log(
        settings=settings,
        admin_id=admin.id,
        report_id=None,
        action="exported",
        detail={
            "export_type": "filtered_on_demand",
            "format": export_format,
            "filters": filters.as_detail_dict(),
            "report_count": document.report_count,
            "truncated": document.truncated,
            "export_limit": EXPORT_REPORT_LIMIT,
        },
    )
    filename = export_filename(filters=filters, export_format=export_format)
    return content, filename, _MEDIA_TYPES[export_format]
