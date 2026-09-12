"""Attachment linkage, ticket thread payload, and proxy delivery tests."""

from __future__ import annotations

import io
from unittest.mock import MagicMock, patch

import pytest
from app.core.ticket_code import hash_ticket_code
from app.main import create_app
from app.services.reporter_reports import FOLLOWUP_PHOTO_MESSAGE
from fastapi.testclient import TestClient
from PIL import Image
from tests.conftest import FIXTURE_ACCESS_CODE

REPORT_B_ID = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
TICKET_B = "EFGH6789"
ATTACHMENT_ID = "cccccccc-cccc-cccc-cccc-cccccccccccc"
MESSAGE_ID = "dddddddd-dddd-dddd-dddd-dddddddddddd"
UPLOADED_AT = "2026-09-03T12:00:00+00:00"
STORAGE_PATH = f"{REPORT_B_ID}/{ATTACHMENT_ID}.png"


@pytest.fixture
def client(api_env: None) -> TestClient:
    return TestClient(create_app())


def _session_cookie(client: TestClient) -> None:
    response = client.post(
        "/api/access/verify",
        json={"access_code": FIXTURE_ACCESS_CODE},
    )
    assert response.status_code == 200


def _minimal_png_bytes() -> bytes:
    image = Image.new("RGB", (2, 2), color="red")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _report_row(*, status: str = "new") -> dict:
    return {
        "id": REPORT_B_ID,
        "status": status,
        "report_type": "complaint",
        "description": "Test report body.",
        "reported_member_name": None,
        "severity": None,
        "created_at": UPLOADED_AT,
        "updated_at": UPLOADED_AT,
        "ticket_code_hash": hash_ticket_code(TICKET_B),
    }


def _attachment_row(*, message_id: str | None = None) -> dict:
    return {
        "id": ATTACHMENT_ID,
        "report_id": REPORT_B_ID,
        "message_id": message_id,
        "storage_path": STORAGE_PATH,
        "file_type": "image/png",
        "uploaded_at": UPLOADED_AT,
    }


@patch("app.services.reporter_reports.insert_attachment")
@patch("app.services.reporter_reports.upload_object")
@patch("app.services.reporter_reports.fetch_report_by_ticket_hash")
def test_initial_upload_does_not_create_message(
    fetch_mock: MagicMock,
    upload_mock: MagicMock,
    insert_mock: MagicMock,
    client: TestClient,
) -> None:
    fetch_mock.return_value = _report_row()
    insert_mock.return_value = _attachment_row()
    _session_cookie(client)
    response = client.post(
        f"/api/reports/ticket/{TICKET_B}/attachments",
        files={"file": ("evidence.png", _minimal_png_bytes(), "image/png")},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["message_id"] is None
    assert body["preview_url"] == (
        f"/api/reports/ticket/{TICKET_B}/attachments/{ATTACHMENT_ID}"
    )
    insert_mock.assert_called_once()
    assert insert_mock.call_args.kwargs.get("message_id") is None


@patch("app.services.reporter_reports.insert_followup_attachment_atomic")
@patch("app.services.reporter_reports.upload_object")
@patch("app.services.reporter_reports.fetch_report_by_ticket_hash")
def test_follow_up_upload_creates_one_message_and_one_attachment(
    fetch_mock: MagicMock,
    upload_mock: MagicMock,
    rpc_mock: MagicMock,
    client: TestClient,
) -> None:
    fetch_mock.return_value = _report_row()
    rpc_mock.return_value = {
        "message_id": MESSAGE_ID,
        "attachment_id": ATTACHMENT_ID,
        "message_created_at": UPLOADED_AT,
        "attachment_uploaded_at": UPLOADED_AT,
        "file_type": "image/png",
    }
    _session_cookie(client)
    response = client.post(
        f"/api/reports/ticket/{TICKET_B}/attachments?link_to_thread=true",
        files={"file": ("evidence.png", _minimal_png_bytes(), "image/png")},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["message_id"] == MESSAGE_ID
    rpc_mock.assert_called_once()
    assert rpc_mock.call_args.kwargs["content"] == FOLLOWUP_PHOTO_MESSAGE
    assert rpc_mock.call_args.kwargs["report_id"] == REPORT_B_ID


@patch("app.services.reporter_reports.insert_followup_attachment_atomic")
@patch("app.services.reporter_reports.upload_object")
@patch("app.services.reporter_reports.fetch_report_by_ticket_hash")
def test_second_follow_up_uses_new_rpc_call_not_first_message(
    fetch_mock: MagicMock,
    upload_mock: MagicMock,
    rpc_mock: MagicMock,
    client: TestClient,
) -> None:
    fetch_mock.return_value = _report_row()
    second_attachment_id = "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"
    second_message_id = "ffffffff-ffff-ffff-ffff-ffffffffffff"
    rpc_mock.side_effect = [
        {
            "message_id": MESSAGE_ID,
            "attachment_id": ATTACHMENT_ID,
            "message_created_at": UPLOADED_AT,
            "attachment_uploaded_at": UPLOADED_AT,
            "file_type": "image/png",
        },
        {
            "message_id": second_message_id,
            "attachment_id": second_attachment_id,
            "message_created_at": UPLOADED_AT,
            "attachment_uploaded_at": UPLOADED_AT,
            "file_type": "image/png",
        },
    ]
    _session_cookie(client)
    first = client.post(
        f"/api/reports/ticket/{TICKET_B}/attachments?link_to_thread=true",
        files={"file": ("one.png", _minimal_png_bytes(), "image/png")},
    )
    second = client.post(
        f"/api/reports/ticket/{TICKET_B}/attachments?link_to_thread=true",
        files={"file": ("two.png", _minimal_png_bytes(), "image/png")},
    )
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["message_id"] == MESSAGE_ID
    assert second.json()["message_id"] == second_message_id
    assert rpc_mock.call_count == 2
    assert (
        rpc_mock.call_args_list[0].kwargs["storage_path"]
        != rpc_mock.call_args_list[1].kwargs["storage_path"]
    )


@patch("app.services.attachment_delivery.download_object")
@patch("app.services.attachment_delivery.fetch_attachment_by_id")
@patch("app.services.attachment_delivery.fetch_report_by_ticket_hash")
def test_attachment_proxy_happy_path(
    fetch_report_mock: MagicMock,
    fetch_attachment_mock: MagicMock,
    download_mock: MagicMock,
    client: TestClient,
) -> None:
    fetch_report_mock.return_value = _report_row()
    fetch_attachment_mock.return_value = _attachment_row()
    download_mock.return_value = (_minimal_png_bytes(), "image/png")
    _session_cookie(client)
    response = client.get(
        f"/api/reports/ticket/{TICKET_B}/attachments/{ATTACHMENT_ID}",
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/png")
    assert response.content == _minimal_png_bytes()


@patch("app.services.attachment_delivery.fetch_attachment_by_id")
@patch("app.services.attachment_delivery.fetch_report_by_ticket_hash")
def test_attachment_proxy_wrong_ticket_code_is_404(
    fetch_report_mock: MagicMock,
    fetch_attachment_mock: MagicMock,
    client: TestClient,
) -> None:
    fetch_report_mock.return_value = _report_row()
    fetch_attachment_mock.return_value = _attachment_row()
    _session_cookie(client)
    response = client.get(
        f"/api/reports/ticket/MNOP3456/attachments/{ATTACHMENT_ID}",
    )
    assert response.status_code == 404


@patch("app.services.reporter_reports.fetch_attachments_for_report")
@patch("app.services.reporter_reports.fetch_messages_for_report")
@patch("app.services.reporter_reports.fetch_report_by_ticket_hash")
def test_ticket_status_includes_report_and_message_attachments(
    fetch_report_mock: MagicMock,
    fetch_messages_mock: MagicMock,
    fetch_attachments_mock: MagicMock,
    client: TestClient,
) -> None:
    fetch_report_mock.return_value = _report_row()
    fetch_messages_mock.return_value = [
        {
            "id": MESSAGE_ID,
            "sender_type": "reporter",
            "content": FOLLOWUP_PHOTO_MESSAGE,
            "created_at": UPLOADED_AT,
        }
    ]
    fetch_attachments_mock.return_value = [
        _attachment_row(message_id=None),
        _attachment_row(message_id=MESSAGE_ID),
    ]
    _session_cookie(client)
    response = client.get(f"/api/reports/ticket/{TICKET_B}")
    assert response.status_code == 200
    body = response.json()
    assert len(body["report_attachments"]) == 1
    assert body["report_attachments"][0]["preview_url"].endswith(ATTACHMENT_ID)
    assert body["messages"][0]["attachment"]["id"] == ATTACHMENT_ID


def test_attachment_message_link_migration_exists() -> None:
    from pathlib import Path

    migration = (
        Path(__file__).resolve().parents[3]
        / "supabase"
        / "migrations"
        / "20260912143000_attachment_message_link.sql"
    )
    sql = migration.read_text(encoding="utf-8")
    assert "message_id UUID NULL" in sql
    assert "create_reporter_followup_attachment" in sql
    assert "ON DELETE CASCADE" in sql
    assert "attachments_message_id_idx" in sql
    assert "REVOKE ALL ON FUNCTION public.create_reporter_followup_attachment" in sql
    assert "FROM PUBLIC, anon, authenticated" in sql
    assert "GRANT EXECUTE ON FUNCTION public.create_reporter_followup_attachment" in sql
    assert "TO service_role" in sql


@patch("app.services.attachment_delivery.fetch_attachment_by_id")
@patch("app.services.attachment_delivery.fetch_report_by_id")
def test_admin_attachment_proxy_rejects_cross_report_attachment(
    fetch_report_mock: MagicMock,
    fetch_attachment_mock: MagicMock,
    api_env: None,
) -> None:
    from app.core.admin_auth import AdminContext
    from app.core.settings import get_settings
    from app.exceptions.reports import ReportNotFoundError
    from app.services.attachment_delivery import fetch_admin_attachment_bytes

    other_report_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    fetch_report_mock.return_value = {"id": other_report_id}
    fetch_attachment_mock.return_value = _attachment_row()
    admin = AdminContext(
        id="11111111-1111-1111-1111-111111111111",
        full_name="Test Admin",
        role="hoh",
        subunit=None,
        aliases=[],
        permissions=["view"],
    )
    settings = get_settings()
    with pytest.raises(ReportNotFoundError):
        fetch_admin_attachment_bytes(
            report_id=other_report_id,
            attachment_id=ATTACHMENT_ID,
            admin=admin,
            settings=settings,
        )
