"""Simple PDF documents for purge summaries and escalation exports."""

from __future__ import annotations

from io import BytesIO
from typing import Any

from fpdf import FPDF


def _safe_text(value: object) -> str:
    text = str(value or "").strip()
    return text.encode("latin-1", errors="replace").decode("latin-1")


class _BasePdf(FPDF):
    def header(self) -> None:
        self.set_font("Helvetica", "B", 12)
        self.cell(0, 10, _safe_text("Hospi Ledger"), ln=True)

    def body_line(self, text: str) -> None:
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
