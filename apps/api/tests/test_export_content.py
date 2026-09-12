"""Unit tests for export content assembly."""

from __future__ import annotations

from app.services.export_content import (
    ExportFilters,
    assemble_filtered_export_document,
    export_filename,
    report_entry_from_row,
)

LINKED_ADMIN_ID = "33333333-3333-3333-3333-333333333333"


def test_report_entry_omits_sensitive_fields() -> None:
    entry = report_entry_from_row(
        {
            "id": "22222222-2222-2222-2222-222222222222",
            "ticket_code_hash": "secret-hash",
            "source": "telegram",
            "reported_member_admin_id": LINKED_ADMIN_ID,
            "assigned_admin_id": LINKED_ADMIN_ID,
            "report_type": "complaint",
            "status": "new",
            "severity": "low",
            "description": "Example",
            "reported_member_name": "Alex",
            "created_at": "2026-09-01T10:00:00Z",
            "updated_at": "2026-09-02T10:00:00Z",
        },
        categories=["Welfare"],
    )
    assert entry.id == "22222222-2222-2222-2222-222222222222"
    assert entry.reported_member_name == "Alex"
    assert entry.updated_at == "2026-09-02T10:00:00Z"
    assert entry.categories == ("Welfare",)
    payload = entry.__dict__
    assert "ticket_code_hash" not in payload
    assert "reported_member_admin_id" not in payload
    assert "source" not in payload


def test_assemble_marks_truncation_at_limit() -> None:
    rows = [
        {"id": f"report-{index}", "report_type": "complaint"} for index in range(200)
    ]
    document = assemble_filtered_export_document(
        rows=rows,
        category_names_by_report={},
        filters=ExportFilters(None, None, None, None),
        export_limit=200,
    )
    assert document.report_count == 200
    assert document.truncated is True


def test_export_filename_reflects_filters() -> None:
    name = export_filename(
        filters=ExportFilters("escalated", "welfare", None, None),
        export_format="pdf",
    )
    assert name.startswith("hospi-export-status-escalated-")
    assert name.endswith(".pdf")
