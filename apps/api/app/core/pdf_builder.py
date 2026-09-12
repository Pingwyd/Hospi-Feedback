"""Simple PDF documents for purge summaries, escalation, and filtered exports."""

from __future__ import annotations

from io import BytesIO
from typing import Any

from fpdf import FPDF

from app.services.export_content import ExportFilters, FilteredExportDocument


def _safe_text(value: object) -> str:
    text = str(value or "").strip()
    return text.encode("latin-1", errors="replace").decode("latin-1")


class _BasePdf(FPDF):
    def header(self) -> None:
        self.set_font("Helvetica", "B", 12)
        self.cell(0, 10, _safe_text("Hospi Ledger"), ln=True)

    def body_line(self, text: str) -> None:
        self.set_x(self.l_margin)
        self.set_font("Helvetica", "", 10)
        self.multi_cell(0, 6, _safe_text(text))


def build_purge_summary_pdf(
    *,
    run_at: str,
    archived_reports: list[dict[str, Any]],
) -> bytes:
    pdf = _BasePdf()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, _safe_text("Scheduled Purge Summary"), ln=True)
    pdf.body_line(f"Run at: {run_at}")
    pdf.body_line(f"Reports archived: {len(archived_reports)}")
    pdf.ln(4)
    for index, report in enumerate(archived_reports, start=1):
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, _safe_text(f"{index}. Report {report.get('id')}"), ln=True)
        pdf.body_line(f"Type: {report.get('report_type', 'N/A')}")
        pdf.body_line(f"Status: {report.get('status', 'N/A')}")
        pdf.body_line(f"Created: {report.get('created_at', 'N/A')}")
        categories = report.get("categories") or []
        if categories:
            pdf.body_line(f"Categories: {', '.join(str(c) for c in categories)}")
        pdf.ln(2)
    buffer = BytesIO()
    pdf.output(buffer)
    return buffer.getvalue()


def build_escalation_export_pdf(
    *,
    report: dict[str, Any],
    categories: list[str],
    contact_name: str,
) -> bytes:
    pdf = _BasePdf()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, _safe_text("Escalation Export (Redacted)"), ln=True)
    pdf.body_line(f"Escalation contact: {contact_name}")
    pdf.body_line(f"Report type: {report.get('report_type', 'N/A')}")
    pdf.body_line(f"Status: {report.get('status', 'N/A')}")
    pdf.body_line(f"Severity: {report.get('severity') or 'N/A'}")
    pdf.body_line(f"Incident date: {report.get('incident_date') or 'N/A'}")
    pdf.body_line(f"Incident location: {report.get('incident_location') or 'N/A'}")
    if categories:
        pdf.body_line(f"Categories: {', '.join(categories)}")
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, _safe_text("Description"), ln=True)
    pdf.body_line(str(report.get("description") or ""))
    member = report.get("reported_member_name")
    if member:
        pdf.ln(2)
        pdf.body_line(f"Named member: {member}")
    buffer = BytesIO()
    pdf.output(buffer)
    return buffer.getvalue()


def _append_filter_lines(pdf: _BasePdf, filters: ExportFilters) -> None:
    pdf.body_line(f"Status: {filters.status or 'All'}")
    pdf.body_line(f"Keyword: {filters.keyword or 'None'}")
    pdf.body_line(f"Created from: {filters.created_from or 'Any'}")
    pdf.body_line(f"Created to: {filters.created_to or 'Any'}")


def build_filtered_export_pdf(document: FilteredExportDocument) -> bytes:
    pdf = _BasePdf()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, _safe_text("Filtered Report Export"), ln=True)
    pdf.body_line(f"Exported at: {document.exported_at}")
    pdf.body_line(f"Reports included: {document.report_count}")
    if document.truncated:
        pdf.body_line(
            f"Export limited to {document.export_limit} reports. "
            "Narrow filters for a complete set."
        )
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, _safe_text("Applied filters"), ln=True)
    _append_filter_lines(pdf, document.filters)
    pdf.ln(4)

    if not document.reports:
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, _safe_text("Results"), ln=True)
        pdf.body_line("No reports matched these filters.")
    else:
        for index, report in enumerate(document.reports, start=1):
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 8, _safe_text(f"Report {index}: {report.id}"), ln=True)
            pdf.body_line(f"Type: {report.report_type}")
            pdf.body_line(f"Status: {report.status}")
            pdf.body_line(f"Severity: {report.severity}")
            pdf.body_line(f"Created: {report.created_at}")
            pdf.body_line(f"Updated: {report.updated_at}")
            pdf.body_line(f"Incident date: {report.incident_date or 'N/A'}")
            pdf.body_line(f"Incident location: {report.incident_location or 'N/A'}")
            if report.categories:
                pdf.body_line(f"Categories: {', '.join(report.categories)}")
            if report.reported_member_name:
                pdf.body_line(f"Named member: {report.reported_member_name}")
            pdf.ln(2)
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 8, _safe_text("Description"), ln=True)
            pdf.body_line(report.description)
            pdf.ln(4)

    buffer = BytesIO()
    pdf.output(buffer)
    return buffer.getvalue()
