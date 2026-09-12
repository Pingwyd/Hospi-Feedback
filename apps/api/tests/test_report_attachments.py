import io
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from app.core.settings import get_settings
from app.core.ticket_code import hash_ticket_code
from app.exceptions.reports import AttachmentRejectedError, ReportNotFoundError
from app.main import create_app
from app.services.reporter_reports import upload_report_attachment
from fastapi.testclient import TestClient
from PIL import Image
from tests.conftest import FIXTURE_ACCESS_CODE

REPORT_A_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
REPORT_B_ID = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
TICKET_A = "ABCD2345"
TICKET_B = "EFGH6789"
UPLOADED_AT = "2026-09-03T12:00:00+00:00"


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


def _report_row(report_id: str, ticket_code: str, *, status: str = "new") -> dict:
    return {
        "id": report_id,
        "status": status,
        "report_type": "complaint",
        "description": "Test report body.",
        "reported_member_name": None,
        "severity": None,
        "created_at": UPLOADED_AT,
        "updated_at": UPLOADED_AT,
        "ticket_code_hash": hash_ticket_code(ticket_code),
    }


@patch("app.services.reporter_reports.insert_attachment")
@patch("app.services.reporter_reports.upload_object")
@patch("app.services.reporter_reports.fetch_report_by_ticket_hash")
def test_upload_attachment_happy_path(
    fetch_mock: MagicMock,
    upload_mock: MagicMock,
    insert_mock: MagicMock,
    client: TestClient,
) -> None:
    fetch_mock.return_value = _report_row(REPORT_B_ID, TICKET_B)
    insert_mock.return_value = {
        "id": "cccccccc-cccc-cccc-cccc-cccccccccccc",
        "file_type": "image/png",
        "uploaded_at": UPLOADED_AT,
        "message_id": None,
    }
    _session_cookie(client)
    response = client.post(
        f"/api/reports/ticket/{TICKET_B}/attachments",
        files={"file": ("evidence.png", _minimal_png_bytes(), "image/png")},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["file_type"] == "image/png"
    assert body["uploaded_at"] == UPLOADED_AT
    upload_mock.assert_called_once()
    insert_mock.assert_called_once()
    assert insert_mock.call_args.kwargs["report_id"] == REPORT_B_ID


@patch("app.services.reporter_reports.count_attachments_for_report")
@patch("app.services.reporter_reports.insert_attachment")
@patch("app.services.reporter_reports.upload_object")
@patch("app.services.reporter_reports.fetch_report_by_ticket_hash")
def test_attachment_ownership_boundary_wrong_code_is_404(
    fetch_mock: MagicMock,
    upload_mock: MagicMock,
    insert_mock: MagicMock,
    count_mock: MagicMock,
    client: TestClient,
) -> None:
    attachment_counts = {REPORT_A_ID: 0, REPORT_B_ID: 0}

    def fetch_side_effect(*, ticket_code_hash: str, **_kwargs: object) -> dict | None:
        if ticket_code_hash == hash_ticket_code(TICKET_A):
            return _report_row(REPORT_A_ID, TICKET_A)
        if ticket_code_hash == hash_ticket_code(TICKET_B):
            return _report_row(REPORT_B_ID, TICKET_B)
        return None

    def insert_side_effect(*, report_id: str, **_kwargs: object) -> dict:
        attachment_counts[report_id] += 1
        return {
            "id": "cccccccc-cccc-cccc-cccc-cccccccccccc",
            "file_type": "image/png",
            "uploaded_at": UPLOADED_AT,
            "message_id": None,
        }

    fetch_mock.side_effect = fetch_side_effect
    insert_mock.side_effect = insert_side_effect
    count_mock.side_effect = lambda *, report_id, **_kwargs: attachment_counts[
        report_id
    ]

    _session_cookie(client)
    wrong_code = "MNOP3456"
    response = client.post(
        f"/api/reports/ticket/{wrong_code}/attachments",
        files={"file": ("evidence.png", _minimal_png_bytes(), "image/png")},
    )
    assert response.status_code == 404
    upload_mock.assert_not_called()
    insert_mock.assert_not_called()
    assert attachment_counts[REPORT_A_ID] == 0
    assert attachment_counts[REPORT_B_ID] == 0

    success = client.post(
        f"/api/reports/ticket/{TICKET_B}/attachments",
        files={"file": ("evidence.png", _minimal_png_bytes(), "image/png")},
    )
    assert success.status_code == 201
    insert_mock.assert_called_once()
    assert insert_mock.call_args.kwargs["report_id"] == REPORT_B_ID
    assert attachment_counts[REPORT_A_ID] == 0
    assert attachment_counts[REPORT_B_ID] == 1


@patch("app.services.reporter_reports.fetch_report_by_ticket_hash")
def test_renamed_non_image_rejected(
    fetch_mock: MagicMock,
    client: TestClient,
) -> None:
    fetch_mock.return_value = _report_row(REPORT_B_ID, TICKET_B)
    _session_cookie(client)
    response = client.post(
        f"/api/reports/ticket/{TICKET_B}/attachments",
        files={"file": ("fake.jpg", b"plain text, not an image", "image/jpeg")},
    )
    assert response.status_code == 415
    assert response.json()["error"]["code"] == "unsupported_media_type"


def test_prepare_image_rejects_fake_jpg(api_env: None) -> None:
    settings = get_settings()
    with patch(
        "app.services.reporter_reports.fetch_report_by_ticket_hash",
        return_value=_report_row(REPORT_B_ID, TICKET_B),
    ):
        with pytest.raises(AttachmentRejectedError):
            upload_report_attachment(
                TICKET_B,
                b"plain text, not an image",
                settings=settings,
            )


@patch("app.api.routes.reports.upload_report_attachment")
def test_wrong_ticket_code_attachment_returns_404(
    upload_mock: MagicMock,
    client: TestClient,
) -> None:
    upload_mock.side_effect = ReportNotFoundError("Report not found.")
    _session_cookie(client)
    response = client.post(
        "/api/reports/ticket/ZZZZZZZZ/attachments",
        files={"file": ("evidence.png", _minimal_png_bytes(), "image/png")},
    )
    assert response.status_code == 404


def test_storage_migration_denies_anon_and_authenticated() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    migration = (
        repo_root
        / "supabase"
        / "migrations"
        / "20260903184000_report_attachments_storage.sql"
    )
    sql = migration.read_text(encoding="utf-8")
    assert "report-attachments" in sql
    assert "false," in sql
    assert "5242880" in sql
    assert "report_attachments_deny_anon" in sql
    assert "report_attachments_deny_authenticated" in sql
    assert "TO anon" in sql
    assert "TO authenticated" in sql
    assert "bucket_id <> 'report-attachments'" in sql
