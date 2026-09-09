"""Tests for admin report triage, recusal enforcement, and audit logging."""

from __future__ import annotations

from unittest.mock import MagicMock, call, patch

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


REPORT_ID = "22222222-2222-2222-2222-222222222222"
OTHER_ADMIN_ID = "33333333-3333-3333-3333-333333333333"


def _report_row(
    *,
    reported_member_name: str | None = "Someone else",
    reported_member_admin_id: str | None = None,
    status: str = "under_review",
) -> dict:
    return {
        "id": REPORT_ID,
        "ticket_code_hash": "hash-fixture",
        "source": "web",
        "report_type": "complaint",
        "reported_member_name": reported_member_name,
        "reported_member_admin_id": reported_member_admin_id,
        "description": "Fixture report",
        "incident_date": None,
        "incident_location": None,
        "severity": "medium",
        "status": status,
        "assigned_admin_id": None,
        "publish_shoutout": False,
        "is_public": False,
        "possible_duplicate_of": None,
        "created_at": "2026-09-01T10:00:00Z",
        "updated_at": "2026-09-01T10:00:00Z",
    }


@pytest.fixture
def client(api_env: None) -> TestClient:
    return TestClient(create_app())


@patch("app.services.recusal_enforcement.write_audit_log")
@patch("app.services.admin_reports.patch_report_fields")
@patch("app.services.admin_reports.fetch_report_by_id")
@patch("app.core.admin_auth.fetch_admin_permissions")
@patch("app.core.admin_auth.fetch_active_admin")
def test_recusal_blocked_returns_409_and_audit_row(
    fetch_admin_mock: MagicMock,
    fetch_permissions_mock: MagicMock,
    fetch_report_mock: MagicMock,
    patch_report_mock: MagicMock,
    recusal_audit_mock: MagicMock,
    client: TestClient,
) -> None:
    fetch_admin_mock.return_value = _named_admin_record()
    fetch_permissions_mock.return_value = frozenset({"close", "view"})
    fetch_report_mock.return_value = _report_row(
        reported_member_name="Ada Okonkwo",
        reported_member_admin_id=ADMIN_ID,
    )
    token = _issue_admin_token()
    response = client.patch(
        f"/api/admin/reports/{REPORT_ID}/status",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": "closed"},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "recusal_blocked"
    patch_report_mock.assert_not_called()
    recusal_audit_mock.assert_called_once()
    assert recusal_audit_mock.call_args.kwargs["action"] == "other"
    assert recusal_audit_mock.call_args.kwargs["detail"] == {"event": "recusal_blocked"}


@patch("app.services.recusal_enforcement.write_audit_log")
@patch("app.services.admin_reports.patch_report_fields")
@patch("app.services.admin_reports.fetch_report_by_id")
@patch("app.core.admin_auth.fetch_admin_permissions")
@patch("app.core.admin_auth.fetch_active_admin")
def test_recusal_warn_requires_confirmation_flag(
    fetch_admin_mock: MagicMock,
    fetch_permissions_mock: MagicMock,
    fetch_report_mock: MagicMock,
    patch_report_mock: MagicMock,
    recusal_audit_mock: MagicMock,
    client: TestClient,
) -> None:
    fetch_admin_mock.return_value = _named_admin_record()
    fetch_permissions_mock.return_value = frozenset({"close", "view"})
    fetch_report_mock.return_value = _report_row(
        reported_member_name="Complaint about ada during hall meeting",
        reported_member_admin_id=None,
    )
    token = _issue_admin_token()
    response = client.patch(
        f"/api/admin/reports/{REPORT_ID}/status",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": "closed", "confirm_recusal_override": False},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "recusal_confirmation_required"
    patch_report_mock.assert_not_called()
    recusal_audit_mock.assert_called_once()
    assert recusal_audit_mock.call_args.kwargs["detail"] == {
        "event": "recusal_warn",
        "confirmed": False,
    }


@patch("app.services.admin_reports.write_audit_log")
@patch("app.services.recusal_enforcement.write_audit_log")
@patch("app.services.admin_reports.patch_report_fields")
@patch("app.services.admin_reports.fetch_report_by_id")
@patch("app.core.admin_auth.fetch_admin_permissions")
@patch("app.core.admin_auth.fetch_active_admin")
def test_recusal_warn_succeeds_with_confirmation_and_marks_closed(
    fetch_admin_mock: MagicMock,
    fetch_permissions_mock: MagicMock,
    fetch_report_mock: MagicMock,
    patch_report_mock: MagicMock,
    recusal_audit_mock: MagicMock,
    audit_mock: MagicMock,
    client: TestClient,
) -> None:
    fetch_admin_mock.return_value = _named_admin_record()
    fetch_permissions_mock.return_value = frozenset({"close", "view"})
    report = _report_row(
        reported_member_name="Complaint about ada during hall meeting",
        reported_member_admin_id=None,
    )
    fetch_report_mock.return_value = report
    patch_report_mock.return_value = {**report, "status": "closed"}
    token = _issue_admin_token()
    response = client.patch(
        f"/api/admin/reports/{REPORT_ID}/status",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": "closed", "confirm_recusal_override": True},
    )
    assert response.status_code == 200
    patch_report_mock.assert_called_once()
    audit_mock.assert_called_once()
    assert audit_mock.call_args.kwargs["action"] == "closed"
    assert audit_mock.call_args.kwargs["detail"]["recusal_override"] is True


@patch("app.services.admin_reports.write_audit_log")
@patch("app.services.admin_reports.patch_report_fields")
@patch("app.services.admin_reports.fetch_report_by_id")
@patch("app.core.admin_auth.fetch_admin_permissions")
@patch("app.core.admin_auth.fetch_active_admin")
def test_normal_status_change_succeeds_without_recusal_audit(
    fetch_admin_mock: MagicMock,
    fetch_permissions_mock: MagicMock,
    fetch_report_mock: MagicMock,
    patch_report_mock: MagicMock,
    audit_mock: MagicMock,
    client: TestClient,
) -> None:
    fetch_admin_mock.return_value = _named_admin_record()
    fetch_permissions_mock.return_value = frozenset({"respond", "view"})
    report = _report_row(reported_member_name="Someone else")
    fetch_report_mock.return_value = report
    patch_report_mock.return_value = {**report, "status": "in_progress"}
    token = _issue_admin_token()
    response = client.patch(
        f"/api/admin/reports/{REPORT_ID}/status",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": "in_progress"},
    )
    assert response.status_code == 200
    audit_mock.assert_called_once()
    assert audit_mock.call_args.kwargs["action"] == "status_changed"


@patch("app.services.admin_reports.write_audit_log")
@patch("app.services.admin_reports.apply_report_status_change")
@patch("app.core.admin_auth.fetch_admin_permissions")
@patch("app.core.admin_auth.fetch_active_admin")
def test_mark_false_route_delegates_to_shared_status_path(
    fetch_admin_mock: MagicMock,
    fetch_permissions_mock: MagicMock,
    apply_mock: MagicMock,
    audit_mock: MagicMock,
    client: TestClient,
) -> None:
    fetch_admin_mock.return_value = _named_admin_record()
    fetch_permissions_mock.return_value = frozenset({"close", "view"})
    apply_mock.return_value = _report_row(status="marked_false")
    token = _issue_admin_token()
    response = client.post(
        f"/api/admin/reports/{REPORT_ID}/mark-false",
        headers={"Authorization": f"Bearer {token}"},
        json={"confirm_recusal_override": True},
    )
    assert response.status_code == 200
    apply_mock.assert_called_once_with(
        report_id=REPORT_ID,
        new_status="marked_false",
        admin=apply_mock.call_args.kwargs["admin"],
        settings=apply_mock.call_args.kwargs["settings"],
        confirm_recusal_override=True,
    )


@patch("app.services.admin_reports.write_audit_log")
@patch("app.services.admin_reports.patch_report_fields")
@patch("app.services.admin_reports.enforce_recusal_for_mutation")
@patch("app.services.admin_reports.fetch_report_by_id")
@patch("app.core.admin_auth.fetch_admin_permissions")
@patch("app.core.admin_auth.fetch_active_admin")
def test_patch_status_marked_false_writes_marked_false_audit_action(
    fetch_admin_mock: MagicMock,
    fetch_permissions_mock: MagicMock,
    fetch_report_mock: MagicMock,
    recusal_mock: MagicMock,
    patch_report_mock: MagicMock,
    audit_mock: MagicMock,
    client: TestClient,
) -> None:
    fetch_admin_mock.return_value = _named_admin_record()
    fetch_permissions_mock.return_value = frozenset({"close", "view"})
    report = _report_row()
    fetch_report_mock.return_value = report
    patch_report_mock.return_value = {**report, "status": "marked_false"}
    token = _issue_admin_token()
    response = client.patch(
        f"/api/admin/reports/{REPORT_ID}/status",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": "marked_false", "confirm_recusal_override": True},
    )
    assert response.status_code == 200
    recusal_mock.assert_called_once()
    audit_mock.assert_called_once()
    assert audit_mock.call_args.kwargs["action"] == "marked_false"


@patch("app.services.admin_reports.archive_report")
@patch("app.services.admin_reports.write_audit_log")
@patch("app.services.admin_reports.fetch_report_by_id")
@patch("app.core.admin_auth.fetch_admin_permissions")
@patch("app.core.admin_auth.fetch_active_admin")
def test_delete_writes_audit_before_archive(
    fetch_admin_mock: MagicMock,
    fetch_permissions_mock: MagicMock,
    fetch_report_mock: MagicMock,
    audit_mock: MagicMock,
    archive_mock: MagicMock,
    client: TestClient,
) -> None:
    fetch_admin_mock.return_value = _named_admin_record()
    fetch_permissions_mock.return_value = frozenset({"view", "close", "manage_admins"})
    fetch_report_mock.return_value = _report_row()
    token = _issue_admin_token()
    manager = MagicMock()
    manager.attach_mock(audit_mock, "audit")
    manager.attach_mock(archive_mock, "archive")
    response = client.request(
        "DELETE",
        f"/api/admin/reports/{REPORT_ID}",
        headers={"Authorization": f"Bearer {token}"},
        json={"delete_reason": "Duplicate test report"},
    )
    assert response.status_code == 204
    assert manager.mock_calls == [
        call.audit(
            settings=audit_mock.call_args.kwargs["settings"],
            admin_id=ADMIN_ID,
            report_id=REPORT_ID,
            action="deleted",
            detail={"delete_reason": "Duplicate test report"},
        ),
        call.archive(
            report_id=REPORT_ID,
            archive_reason="admin_deleted",
            settings=archive_mock.call_args.kwargs["settings"],
            deleted_by_admin_id=ADMIN_ID,
            delete_reason="Duplicate test report",
        ),
    ]


@patch("app.services.admin_reports.archive_report")
@patch("app.services.admin_reports.write_audit_log")
@patch("app.services.admin_reports.fetch_report_by_id")
@patch("app.core.admin_auth.fetch_admin_permissions")
@patch("app.core.admin_auth.fetch_active_admin")
def test_delete_rejects_non_hoh_even_with_manage_admins(
    fetch_admin_mock: MagicMock,
    fetch_permissions_mock: MagicMock,
    fetch_report_mock: MagicMock,
    audit_mock: MagicMock,
    archive_mock: MagicMock,
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
    fetch_permissions_mock.return_value = frozenset({"manage_admins", "view", "close"})
    fetch_report_mock.return_value = _report_row()
    token = _issue_admin_token()
    response = client.request(
        "DELETE",
        f"/api/admin/reports/{REPORT_ID}",
        headers={"Authorization": f"Bearer {token}"},
        json={"delete_reason": "Should fail"},
    )
    assert response.status_code == 403
    audit_mock.assert_not_called()
    archive_mock.assert_not_called()
