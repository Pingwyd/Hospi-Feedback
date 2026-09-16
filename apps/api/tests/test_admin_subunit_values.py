"""Tests for admin subunit enum validation on create."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from app.exceptions.admin_reports import AdminReportValidationError
from app.integrations.supabase_rest import AdminRecord
from app.main import create_app
from app.services.admin_subunits import validate_admin_subunit_for_create
from fastapi.testclient import TestClient
from tests.test_admin_auth import ADMIN_ID, _issue_admin_token


@pytest.fixture
def client(api_env: None) -> TestClient:
    return TestClient(create_app())


def test_validate_subunit_required_for_subunit_head() -> None:
    with pytest.raises(AdminReportValidationError, match="required"):
        validate_admin_subunit_for_create("subunit_head", None)


def test_validate_subunit_rejects_unknown_enum() -> None:
    with pytest.raises(AdminReportValidationError, match="Invalid subunit"):
        validate_admin_subunit_for_create("subunit_head", "unknown_team")


def test_validate_subunit_accepts_canonical_value() -> None:
    assert validate_admin_subunit_for_create("subunit_asst", "welfare") == "welfare"


def test_validate_subunit_rejects_value_for_hoh() -> None:
    with pytest.raises(AdminReportValidationError, match="must be omitted"):
        validate_admin_subunit_for_create("hoh", "welfare")


def test_validate_subunit_allows_null_for_custom() -> None:
    assert validate_admin_subunit_for_create("custom", None) is None


@patch("app.core.admin_auth.fetch_admin_permissions")
@patch("app.core.admin_auth.fetch_active_admin")
def test_create_admin_rejects_subunit_for_hoh(
    fetch_admin_mock: MagicMock,
    fetch_permissions_mock: MagicMock,
    client: TestClient,
) -> None:
    fetch_admin_mock.return_value = AdminRecord(
        id=ADMIN_ID,
        full_name="Manager",
        role="hoh",
        subunit=None,
        aliases=(),
        active=True,
    )
    fetch_permissions_mock.return_value = frozenset({"manage_admins"})
    token = _issue_admin_token()

    response = client.post(
        "/api/admin/admins",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "email": "new.admin@example.com",
            "password": "longpassword12",
            "full_name": "New Admin",
            "role": "hoh",
            "subunit": "welfare",
            "permissions": [],
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


@patch("app.core.admin_auth.fetch_admin_permissions")
@patch("app.core.admin_auth.fetch_active_admin")
def test_create_admin_requires_subunit_for_subunit_head(
    fetch_admin_mock: MagicMock,
    fetch_permissions_mock: MagicMock,
    client: TestClient,
) -> None:
    fetch_admin_mock.return_value = AdminRecord(
        id=ADMIN_ID,
        full_name="Manager",
        role="hoh",
        subunit=None,
        aliases=(),
        active=True,
    )
    fetch_permissions_mock.return_value = frozenset({"manage_admins"})
    token = _issue_admin_token()

    response = client.post(
        "/api/admin/admins",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "email": "sub.head@example.com",
            "password": "longpassword12",
            "full_name": "Sub Head",
            "role": "subunit_head",
            "subunit": None,
            "permissions": [],
        },
    )

    assert response.status_code == 422
