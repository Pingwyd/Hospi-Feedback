"""Step 2 admin support routes: WS, admins CRUD, audit viewer, stats."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from app.integrations.supabase_rest import AdminRecord
from app.main import create_app
from app.services.reporter_reports import CreateReportResult
from fastapi.testclient import TestClient
from tests.conftest import FIXTURE_ACCESS_CODE
from tests.test_admin_auth import ADMIN_ID, _issue_admin_token

REPORT_ID = "22222222-2222-2222-2222-222222222222"


@pytest.fixture
def client(api_env: None) -> TestClient:
    return TestClient(create_app())


def _admin_record(*, role: str = "hoh", permissions: frozenset[str]) -> AdminRecord:
    return AdminRecord(
        id=ADMIN_ID,
        full_name="Local Bootstrap HOH",
        role=role,
        subunit=None,
        aliases=("HOH",),
        active=True,
    )


@patch("app.core.admin_auth.fetch_admin_permissions")
@patch("app.core.admin_auth.fetch_active_admin")
def test_admins_list_forbidden_without_manage_admins(
    fetch_admin_mock: MagicMock,
    fetch_permissions_mock: MagicMock,
    client: TestClient,
) -> None:
    fetch_admin_mock.return_value = _admin_record(permissions=frozenset({"view"}))
    fetch_permissions_mock.return_value = frozenset({"view"})
    token = _issue_admin_token()
    response = client.get(
        "/api/admin/admins",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "forbidden"


@patch("app.api.routes.admin_management.list_admin_users")
@patch("app.core.admin_auth.fetch_admin_permissions")
@patch("app.core.admin_auth.fetch_active_admin")
def test_admins_list_allowed_with_manage_admins(
    fetch_admin_mock: MagicMock,
    fetch_permissions_mock: MagicMock,
    list_admin_users_mock: MagicMock,
    client: TestClient,
) -> None:
    fetch_admin_mock.return_value = _admin_record(
        permissions=frozenset({"view", "manage_admins"})
    )
    fetch_permissions_mock.return_value = frozenset({"view", "manage_admins"})
    list_admin_users_mock.return_value = [
        {
            "id": ADMIN_ID,
            "full_name": "Local Bootstrap HOH",
            "role": "hoh",
            "permissions": ["view"],
        }
    ]
    token = _issue_admin_token()
    response = client.get(
        "/api/admin/admins",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["data"][0]["permissions"] == ["view"]


@patch("app.core.admin_auth.fetch_admin_permissions")
@patch("app.core.admin_auth.fetch_active_admin")
def test_audit_log_forbidden_for_non_viewer_role(
    fetch_admin_mock: MagicMock,
    fetch_permissions_mock: MagicMock,
    client: TestClient,
) -> None:
    fetch_admin_mock.return_value = AdminRecord(
        id=ADMIN_ID,
        full_name="Subunit Head",
        role="subunit_head",
        subunit="welfare",
        aliases=(),
        active=True,
    )
    fetch_permissions_mock.return_value = frozenset({"view"})
    token = _issue_admin_token()
    response = client.get(
        "/api/admin/audit-log",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


@patch("app.services.admin_audit.list_audit_log_entries")
@patch("app.core.admin_auth.fetch_admin_permissions")
@patch("app.core.admin_auth.fetch_active_admin")
def test_audit_log_allowed_for_asst_head(
    fetch_admin_mock: MagicMock,
    fetch_permissions_mock: MagicMock,
    list_audit_mock: MagicMock,
    client: TestClient,
) -> None:
    fetch_admin_mock.return_value = AdminRecord(
        id=ADMIN_ID,
        full_name="Assistant Head",
        role="asst_head",
        subunit=None,
        aliases=(),
        active=True,
    )
    fetch_permissions_mock.return_value = frozenset({"view"})
    list_audit_mock.return_value = [
        {
            "id": "99999999-9999-9999-9999-999999999999",
            "admin_id": ADMIN_ID,
            "report_id": REPORT_ID,
            "action": "status_changed",
            "detail": {},
            "created_at": "2026-09-01T10:00:00Z",
        }
    ]
    token = _issue_admin_token()
    response = client.get(
        "/api/admin/audit-log",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["data"][0]["action"] == "status_changed"


@patch("app.core.admin_auth.fetch_admin_permissions")
@patch("app.core.admin_auth.fetch_active_admin")
def test_admin_me_returns_profile(
    fetch_admin_mock: MagicMock,
    fetch_permissions_mock: MagicMock,
    client: TestClient,
) -> None:
    fetch_admin_mock.return_value = _admin_record(
        permissions=frozenset({"view", "respond"})
    )
    fetch_permissions_mock.return_value = frozenset({"view", "respond"})
    token = _issue_admin_token()
    response = client.get(
        "/api/admin/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()["data"]
    assert body["id"] == ADMIN_ID
    assert set(body["permissions"]) == {"respond", "view"}


def _session_cookie(client: TestClient) -> None:
    response = client.post(
        "/api/access/verify",
        json={"access_code": FIXTURE_ACCESS_CODE},
    )
    assert response.status_code == 200


@patch("app.api.routes.reports.create_report")
@patch("app.core.admin_auth.fetch_admin_permissions")
@patch("app.core.admin_auth.fetch_active_admin")
def test_websocket_receives_new_report_event(
    fetch_admin_mock: MagicMock,
    fetch_permissions_mock: MagicMock,
    create_report_mock: MagicMock,
    client: TestClient,
) -> None:
    fetch_admin_mock.return_value = _admin_record(permissions=frozenset({"view"}))
    fetch_permissions_mock.return_value = frozenset({"view"})
    create_report_mock.return_value = CreateReportResult(
        report_id=REPORT_ID,
        ticket_code="ABCD2345EFGH",
        status="new",
        created_at="2026-09-01T10:00:00Z",
    )
    _session_cookie(client)
    token = _issue_admin_token()
    with client.websocket_connect(f"/api/admin/ws?access_token={token}") as ws:
        response = client.post(
            "/api/reports",
            json={
                "report_type": "complaint",
                "description": "Live inbox test",
            },
        )
        assert response.status_code == 201
        event = ws.receive_json()
        assert event["event"] == "new_report"
        assert event["payload"]["report_id"] == REPORT_ID
