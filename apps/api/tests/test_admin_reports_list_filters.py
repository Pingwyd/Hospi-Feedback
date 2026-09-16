"""Tests for GET /api/admin/reports list filter params and validation."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from app.integrations.supabase_rest import AdminRecord
from app.main import create_app
from fastapi.testclient import TestClient
from tests.test_admin_auth import ADMIN_ID, _issue_admin_token


def _named_admin_record() -> AdminRecord:
    return AdminRecord(
        id=ADMIN_ID,
        full_name="Ada Okonkwo",
        role="hoh",
        subunit=None,
        aliases=("Ada",),
        active=True,
    )


def _report_row(**overrides: object) -> dict:
    row = {
        "id": "22222222-2222-2222-2222-222222222222",
        "ticket_code_hash": "hash-fixture",
        "source": "web",
        "report_type": "complaint",
        "reported_member_name": "Someone",
        "reported_member_admin_id": None,
        "description": "Fixture report",
        "incident_date": None,
        "incident_location": None,
        "severity": "medium",
        "status": "new",
        "assigned_admin_id": None,
        "publish_shoutout": False,
        "is_public": False,
        "possible_duplicate_of": None,
        "created_at": "2026-09-01T10:00:00Z",
        "updated_at": "2026-09-01T10:00:00Z",
    }
    row.update(overrides)
    return row


@pytest.fixture
def client(api_env: None) -> TestClient:
    return TestClient(create_app())


@pytest.fixture
def admin_mocks() -> tuple[MagicMock, MagicMock]:
    with (
        patch("app.core.admin_auth.fetch_active_admin") as fetch_admin,
        patch("app.core.admin_auth.fetch_admin_permissions") as fetch_permissions,
    ):
        fetch_admin.return_value = _named_admin_record()
        fetch_permissions.return_value = frozenset({"view"})
        yield fetch_admin, fetch_permissions


@patch("app.services.admin_reports.list_reports")
def test_list_reports_filter_by_report_type(
    list_reports_mock: MagicMock,
    client: TestClient,
    admin_mocks: tuple[MagicMock, MagicMock],
) -> None:
    list_reports_mock.return_value = [_report_row(report_type="complaint")]
    token = _issue_admin_token()

    response = client.get(
        "/api/admin/reports?report_type=complaint",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["data"][0]["report_type"] == "complaint"
    assert list_reports_mock.call_args.kwargs["report_type"] == "complaint"
    assert list_reports_mock.call_args.kwargs["severity"] is None


@patch("app.services.admin_reports.list_reports")
def test_list_reports_filter_by_severity(
    list_reports_mock: MagicMock,
    client: TestClient,
    admin_mocks: tuple[MagicMock, MagicMock],
) -> None:
    list_reports_mock.return_value = [_report_row(severity="high")]
    token = _issue_admin_token()

    response = client.get(
        "/api/admin/reports?severity=high",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert list_reports_mock.call_args.kwargs["severity"] == "high"


@patch("app.services.admin_reports.list_reports")
def test_list_reports_combined_filters(
    list_reports_mock: MagicMock,
    client: TestClient,
    admin_mocks: tuple[MagicMock, MagicMock],
) -> None:
    list_reports_mock.return_value = [_report_row()]
    token = _issue_admin_token()

    response = client.get(
        "/api/admin/reports"
        "?status=new&keyword=welfare&report_type=suggestion&severity=low"
        "&created_from=2026-01-01&created_to=2026-01-31",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    kwargs = list_reports_mock.call_args.kwargs
    assert kwargs["status"] == "new"
    assert kwargs["keyword"] == "welfare"
    assert kwargs["report_type"] == "suggestion"
    assert kwargs["severity"] == "low"
    assert kwargs["created_from"] == "2026-01-01"
    assert kwargs["created_to"] == "2026-01-31"


@patch("app.services.admin_reports.list_reports")
def test_list_reports_invalid_report_type_returns_422(
    list_reports_mock: MagicMock,
    client: TestClient,
    admin_mocks: tuple[MagicMock, MagicMock],
) -> None:
    token = _issue_admin_token()

    response = client.get(
        "/api/admin/reports?report_type=incident",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422
    assert "report_type" in response.json()["error"]["message"].lower()
    list_reports_mock.assert_not_called()


@patch("app.services.admin_reports.list_reports")
def test_list_reports_invalid_severity_returns_422(
    list_reports_mock: MagicMock,
    client: TestClient,
    admin_mocks: tuple[MagicMock, MagicMock],
) -> None:
    token = _issue_admin_token()

    response = client.get(
        "/api/admin/reports?severity=critical",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422
    assert "severity" in response.json()["error"]["message"].lower()
    list_reports_mock.assert_not_called()


@patch("app.services.admin_reports.list_reports")
def test_list_reports_invalid_status_returns_422(
    list_reports_mock: MagicMock,
    client: TestClient,
    admin_mocks: tuple[MagicMock, MagicMock],
) -> None:
    token = _issue_admin_token()

    response = client.get(
        "/api/admin/reports?status=archived",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422
    assert "status" in response.json()["error"]["message"].lower()
    list_reports_mock.assert_not_called()


@patch("app.core.admin_auth.fetch_active_admin")
@patch("app.core.admin_auth.fetch_admin_permissions")
def test_list_reports_without_view_permission_returns_403(
    fetch_permissions_mock: MagicMock,
    fetch_admin_mock: MagicMock,
    client: TestClient,
) -> None:
    fetch_admin_mock.return_value = _named_admin_record()
    fetch_permissions_mock.return_value = frozenset({"export"})
    token = _issue_admin_token()

    response = client.get(
        "/api/admin/reports?report_type=complaint",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
