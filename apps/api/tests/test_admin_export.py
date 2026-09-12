"""Tests for filtered on-demand admin export."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from app.integrations.supabase_rest import AdminRecord
from app.main import create_app
from fastapi.testclient import TestClient
from tests.test_admin_auth import ADMIN_ID, _issue_admin_token

REPORT_ID = "22222222-2222-2222-2222-222222222222"
LINKED_ADMIN_ID = "33333333-3333-3333-3333-333333333333"


def _admin_record() -> AdminRecord:
    return AdminRecord(
        id=ADMIN_ID,
        full_name="Local Bootstrap HOH",
        role="hoh",
        subunit=None,
        aliases=("HOH",),
        active=True,
    )


def _report_row(
    *,
    report_id: str = REPORT_ID,
    status: str = "escalated",
    description: str = "Welfare concern in hall B",
    reported_member_name: str = "Alex Member",
) -> dict:
    return {
        "id": report_id,
        "ticket_code_hash": "hash-must-not-export",
        "source": "telegram",
        "report_type": "complaint",
        "reported_member_name": reported_member_name,
        "reported_member_admin_id": LINKED_ADMIN_ID,
        "description": description,
        "incident_date": "2026-09-01",
        "incident_location": "Main hall",
        "severity": "high",
        "status": status,
        "assigned_admin_id": ADMIN_ID,
        "publish_shoutout": False,
        "is_public": False,
        "possible_duplicate_of": None,
        "created_at": "2026-09-01T10:00:00Z",
        "updated_at": "2026-09-02T12:00:00Z",
    }


@pytest.fixture
def client(api_env: None) -> TestClient:
    return TestClient(create_app())


@patch("app.services.admin_export.write_audit_log")
@patch("app.services.admin_export.fetch_category_names_for_reports")
@patch("app.services.admin_export.list_reports")
@patch("app.core.admin_auth.fetch_admin_permissions")
@patch("app.core.admin_auth.fetch_active_admin")
def test_export_all_reports_pdf(
    fetch_admin_mock: MagicMock,
    fetch_permissions_mock: MagicMock,
    list_reports_mock: MagicMock,
    fetch_categories_mock: MagicMock,
    audit_mock: MagicMock,
    client: TestClient,
) -> None:
    fetch_admin_mock.return_value = _admin_record()
    fetch_permissions_mock.return_value = frozenset({"view", "export"})
    list_reports_mock.return_value = [_report_row()]
    fetch_categories_mock.return_value = {REPORT_ID: ["Welfare"]}
    token = _issue_admin_token()

    response = client.get(
        "/api/admin/export",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "hospi-export-all-" in response.headers["content-disposition"]
    assert response.content.startswith(b"%PDF")
    assert len(response.content) > 500
    list_reports_mock.assert_called_once()
    assert list_reports_mock.call_args.kwargs["status"] is None
    audit_mock.assert_called_once()
    assert audit_mock.call_args.kwargs["action"] == "exported"
    assert audit_mock.call_args.kwargs["report_id"] is None
    detail = audit_mock.call_args.kwargs["detail"]
    assert detail["report_count"] == 1
    assert detail["format"] == "pdf"
    assert detail["filters"]["status"] is None


@patch("app.services.admin_export.write_audit_log")
@patch("app.services.admin_export.fetch_category_names_for_reports")
@patch("app.services.admin_export.list_reports")
@patch("app.core.admin_auth.fetch_admin_permissions")
@patch("app.core.admin_auth.fetch_active_admin")
def test_export_with_status_filter(
    fetch_admin_mock: MagicMock,
    fetch_permissions_mock: MagicMock,
    list_reports_mock: MagicMock,
    fetch_categories_mock: MagicMock,
    audit_mock: MagicMock,
    client: TestClient,
) -> None:
    fetch_admin_mock.return_value = _admin_record()
    fetch_permissions_mock.return_value = frozenset({"view", "export"})
    list_reports_mock.return_value = [_report_row(status="escalated")]
    fetch_categories_mock.return_value = {REPORT_ID: []}
    token = _issue_admin_token()

    response = client.get(
        "/api/admin/export?status=escalated",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert "hospi-export-status-escalated-" in response.headers["content-disposition"]
    assert list_reports_mock.call_args.kwargs["status"] == "escalated"
    assert audit_mock.call_args.kwargs["detail"]["filters"]["status"] == "escalated"


@patch("app.services.admin_export.write_audit_log")
@patch("app.services.admin_export.fetch_category_names_for_reports")
@patch("app.services.admin_export.list_reports")
@patch("app.core.admin_auth.fetch_admin_permissions")
@patch("app.core.admin_auth.fetch_active_admin")
def test_export_with_keyword_filter(
    fetch_admin_mock: MagicMock,
    fetch_permissions_mock: MagicMock,
    list_reports_mock: MagicMock,
    fetch_categories_mock: MagicMock,
    audit_mock: MagicMock,
    client: TestClient,
) -> None:
    fetch_admin_mock.return_value = _admin_record()
    fetch_permissions_mock.return_value = frozenset({"view", "export"})
    list_reports_mock.return_value = [
        _report_row(description="Keyword match welfare issue")
    ]
    fetch_categories_mock.return_value = {REPORT_ID: []}
    token = _issue_admin_token()

    response = client.get(
        "/api/admin/export?keyword=welfare",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert "keyword" in response.headers["content-disposition"]
    assert list_reports_mock.call_args.kwargs["keyword"] == "welfare"
    assert audit_mock.call_args.kwargs["detail"]["filters"]["keyword"] == "welfare"
    assert response.content.startswith(b"%PDF")


@patch("app.services.admin_export.write_audit_log")
@patch("app.services.admin_export.fetch_category_names_for_reports")
@patch("app.services.admin_export.list_reports")
@patch("app.core.admin_auth.fetch_admin_permissions")
@patch("app.core.admin_auth.fetch_active_admin")
def test_export_zero_results_returns_valid_pdf(
    fetch_admin_mock: MagicMock,
    fetch_permissions_mock: MagicMock,
    list_reports_mock: MagicMock,
    fetch_categories_mock: MagicMock,
    audit_mock: MagicMock,
    client: TestClient,
) -> None:
    fetch_admin_mock.return_value = _admin_record()
    fetch_permissions_mock.return_value = frozenset({"view", "export"})
    list_reports_mock.return_value = []
    fetch_categories_mock.return_value = {}
    token = _issue_admin_token()

    response = client.get(
        "/api/admin/export?status=closed",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.content.startswith(b"%PDF")
    assert audit_mock.call_args.kwargs["detail"]["report_count"] == 0
    fetch_categories_mock.assert_not_called()


@patch("app.services.admin_export.write_audit_log")
@patch("app.services.admin_export.fetch_category_names_for_reports")
@patch("app.services.admin_export.list_reports")
@patch("app.core.admin_auth.fetch_admin_permissions")
@patch("app.core.admin_auth.fetch_active_admin")
def test_export_docx_format(
    fetch_admin_mock: MagicMock,
    fetch_permissions_mock: MagicMock,
    list_reports_mock: MagicMock,
    fetch_categories_mock: MagicMock,
    audit_mock: MagicMock,
    client: TestClient,
) -> None:
    fetch_admin_mock.return_value = _admin_record()
    fetch_permissions_mock.return_value = frozenset({"view", "export"})
    list_reports_mock.return_value = [_report_row()]
    fetch_categories_mock.return_value = {REPORT_ID: ["Welfare"]}
    token = _issue_admin_token()

    response = client.get(
        "/api/admin/export?format=docx",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.content.startswith(b"PK")
    assert ".docx" in response.headers["content-disposition"]
    assert audit_mock.call_args.kwargs["detail"]["format"] == "docx"

    from io import BytesIO

    from docx import Document

    doc = Document(BytesIO(response.content))
    doc_text = "\n".join(paragraph.text for paragraph in doc.paragraphs)
    assert REPORT_ID in doc_text
    assert "Welfare concern in hall B" in doc_text
    assert "Alex Member" in doc_text
    assert "hash-must-not-export" not in doc_text
    assert LINKED_ADMIN_ID not in doc_text
    assert "telegram" not in doc_text.lower()


@patch("app.core.admin_auth.fetch_admin_permissions")
@patch("app.core.admin_auth.fetch_active_admin")
def test_export_forbidden_without_permission(
    fetch_admin_mock: MagicMock,
    fetch_permissions_mock: MagicMock,
    client: TestClient,
) -> None:
    fetch_admin_mock.return_value = _admin_record()
    fetch_permissions_mock.return_value = frozenset({"view"})
    token = _issue_admin_token()

    response = client.get(
        "/api/admin/export",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "forbidden"
