"""BL-001-equivalent checks for POST .../attachments/batch."""

from __future__ import annotations

import io
from unittest.mock import MagicMock, patch

import pytest
from app.core.image_upload import prepare_image_for_storage
from app.core.settings import get_settings
from app.core.ticket_code import hash_ticket_code
from app.exceptions.reports import AttachmentRejectedError
from app.main import create_app
from app.services.reporter_reports import upload_followup_attachments_batch
from fastapi.testclient import TestClient
from PIL import Image
from tests.conftest import FIXTURE_ACCESS_CODE

REPORT_A_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
REPORT_B_ID = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
TICKET_A = "ABCD2345"
TICKET_B = "EFGH6789"
MESSAGE_ID = "dddddddd-dddd-dddd-dddd-dddddddddddd"
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


def _jpeg_with_exif_bytes() -> bytes:
    image = Image.new("RGB", (4, 4), color="green")
    exif = image.getexif()
    exif[0x010E] = "hospi-batch-exif-marker"
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", exif=exif)
    raw = buffer.getvalue()
    assert b"Exif" in raw
    return raw


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


def _exif_is_empty(image_bytes: bytes) -> bool:
    image = Image.open(io.BytesIO(image_bytes))
    exif = image.getexif()
    return len(exif) == 0


@patch("app.services.reporter_reports.count_attachments_for_report")
@patch("app.services.reporter_reports.insert_attachment")
@patch("app.services.reporter_reports.insert_reporter_message")
@patch("app.services.reporter_reports.upload_object")
@patch("app.services.reporter_reports.fetch_report_by_ticket_hash")
def test_batch_ownership_boundary_wrong_ticket_code_is_404(
    fetch_mock: MagicMock,
    upload_mock: MagicMock,
    insert_message_mock: MagicMock,
    insert_attachment_mock: MagicMock,
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
            "message_id": MESSAGE_ID,
        }

    fetch_mock.side_effect = fetch_side_effect
    insert_message_mock.return_value = {
        "id": MESSAGE_ID,
        "sender_type": "reporter",
        "content": "Photo attached",
        "created_at": UPLOADED_AT,
    }
    insert_attachment_mock.side_effect = insert_side_effect
    count_mock.side_effect = lambda *, report_id, **_kwargs: attachment_counts[
        report_id
    ]

    _session_cookie(client)
    wrong_code = "MNOP3456"
    png = _minimal_png_bytes()
    response = client.post(
        f"/api/reports/ticket/{wrong_code}/attachments/batch",
        files=[
            ("files", ("one.png", png, "image/png")),
            ("files", ("two.png", png, "image/png")),
        ],
    )
    assert response.status_code == 404
    upload_mock.assert_not_called()
    insert_message_mock.assert_not_called()
    insert_attachment_mock.assert_not_called()
    assert attachment_counts[REPORT_A_ID] == 0
    assert attachment_counts[REPORT_B_ID] == 0

    success = client.post(
        f"/api/reports/ticket/{TICKET_B}/attachments/batch",
        files=[
            ("files", ("one.png", png, "image/png")),
            ("files", ("two.png", png, "image/png")),
        ],
    )
    assert success.status_code == 201
    assert insert_message_mock.call_count == 1
    assert insert_attachment_mock.call_count == 2
    assert attachment_counts[REPORT_A_ID] == 0
    assert attachment_counts[REPORT_B_ID] == 2


@patch("app.services.reporter_reports.delete_message_by_id")
@patch("app.services.reporter_reports.delete_attachment_by_id")
@patch("app.services.reporter_reports.delete_object")
@patch("app.services.reporter_reports.insert_attachment")
@patch("app.services.reporter_reports.insert_reporter_message")
@patch("app.services.reporter_reports.upload_object")
@patch("app.services.reporter_reports.fetch_report_by_ticket_hash")
def test_batch_rejects_renamed_non_image_per_file_and_rolls_back(
    fetch_mock: MagicMock,
    upload_mock: MagicMock,
    insert_message_mock: MagicMock,
    insert_attachment_mock: MagicMock,
    delete_object_mock: MagicMock,
    delete_attachment_mock: MagicMock,
    delete_message_mock: MagicMock,
    client: TestClient,
) -> None:
    fetch_mock.return_value = _report_row(REPORT_B_ID, TICKET_B)
    insert_message_mock.return_value = {
        "id": MESSAGE_ID,
        "sender_type": "reporter",
        "content": "Photo attached",
        "created_at": UPLOADED_AT,
    }
    insert_attachment_mock.return_value = {
        "id": "11111111-1111-1111-1111-111111111111",
        "file_type": "image/png",
        "uploaded_at": UPLOADED_AT,
    }
    _session_cookie(client)
    png = _minimal_png_bytes()
    response = client.post(
        f"/api/reports/ticket/{TICKET_B}/attachments/batch",
        files=[
            ("files", ("good.png", png, "image/png")),
            ("files", ("fake.jpg", b"plain text, not an image", "image/jpeg")),
        ],
    )
    assert response.status_code == 415
    assert response.json()["error"]["code"] == "unsupported_media_type"
    insert_message_mock.assert_called_once()
    upload_mock.assert_called_once()
    insert_attachment_mock.assert_called_once()
    delete_object_mock.assert_called_once()
    delete_attachment_mock.assert_called_once()
    delete_message_mock.assert_called_once()
    assert delete_message_mock.call_args.kwargs["message_id"] == MESSAGE_ID


@patch("app.services.reporter_reports.delete_message_by_id")
@patch("app.services.reporter_reports.delete_attachment_by_id")
@patch("app.services.reporter_reports.delete_object")
@patch("app.services.reporter_reports.insert_attachment")
@patch("app.services.reporter_reports.insert_reporter_message")
@patch("app.services.reporter_reports.upload_object")
@patch("app.services.reporter_reports.fetch_report_by_ticket_hash")
def test_batch_invalid_later_file_rolls_back_earlier_uploads(
    fetch_mock: MagicMock,
    upload_mock: MagicMock,
    insert_message_mock: MagicMock,
    insert_attachment_mock: MagicMock,
    delete_object_mock: MagicMock,
    delete_attachment_mock: MagicMock,
    delete_message_mock: MagicMock,
    api_env: None,
) -> None:
    _ = api_env
    client = TestClient(create_app(), raise_server_exceptions=False)
    fetch_mock.return_value = _report_row(REPORT_B_ID, TICKET_B)
    insert_message_mock.return_value = {
        "id": MESSAGE_ID,
        "sender_type": "reporter",
        "content": "Photo attached",
        "created_at": UPLOADED_AT,
    }
    insert_attachment_mock.side_effect = [
        {
            "id": "11111111-1111-1111-1111-111111111111",
            "file_type": "image/png",
            "uploaded_at": UPLOADED_AT,
        },
        RuntimeError("simulated insert failure"),
    ]
    _session_cookie(client)
    png = _minimal_png_bytes()
    response = client.post(
        f"/api/reports/ticket/{TICKET_B}/attachments/batch",
        files=[
            ("files", ("one.png", png, "image/png")),
            ("files", ("two.png", png, "image/png")),
        ],
    )
    assert response.status_code == 500
    assert upload_mock.call_count == 2
    assert delete_object_mock.call_count == 2
    delete_attachment_mock.assert_called_once()
    delete_message_mock.assert_called_once()
    assert delete_message_mock.call_args.kwargs["message_id"] == MESSAGE_ID


def test_prepare_image_strips_exif(api_env: None) -> None:
    settings = get_settings()
    raw = _jpeg_with_exif_bytes()
    stripped, mime, extension = prepare_image_for_storage(
        raw,
        max_bytes=settings.report_attachment_max_bytes,
    )
    assert mime == "image/jpeg"
    assert extension == "jpg"
    assert _exif_is_empty(stripped)


@patch("app.services.reporter_reports.insert_attachment")
@patch("app.services.reporter_reports.insert_reporter_message")
@patch("app.services.reporter_reports.upload_object")
@patch("app.services.reporter_reports.fetch_report_by_ticket_hash")
def test_batch_strips_exif_on_each_uploaded_object(
    fetch_mock: MagicMock,
    upload_mock: MagicMock,
    insert_message_mock: MagicMock,
    insert_attachment_mock: MagicMock,
    client: TestClient,
) -> None:
    fetch_mock.return_value = _report_row(REPORT_B_ID, TICKET_B)
    insert_message_mock.return_value = {
        "id": MESSAGE_ID,
        "sender_type": "reporter",
        "content": "Photo attached",
        "created_at": UPLOADED_AT,
    }
    insert_attachment_mock.side_effect = [
        {
            "id": "11111111-1111-1111-1111-111111111111",
            "file_type": "image/jpeg",
            "uploaded_at": UPLOADED_AT,
        },
        {
            "id": "22222222-2222-2222-2222-222222222222",
            "file_type": "image/jpeg",
            "uploaded_at": UPLOADED_AT,
        },
    ]
    uploaded_contents: list[bytes] = []

    def capture_upload(*, content: bytes, **_kwargs: object) -> None:
        uploaded_contents.append(content)

    upload_mock.side_effect = capture_upload

    _session_cookie(client)
    jpeg = _jpeg_with_exif_bytes()
    response = client.post(
        f"/api/reports/ticket/{TICKET_B}/attachments/batch",
        files=[
            ("files", ("one.jpg", jpeg, "image/jpeg")),
            ("files", ("two.jpg", jpeg, "image/jpeg")),
        ],
    )
    assert response.status_code == 201
    assert len(uploaded_contents) == 2
    assert all(_exif_is_empty(content) for content in uploaded_contents)


@patch("app.services.reporter_reports.insert_followup_attachment_atomic")
@patch("app.services.reporter_reports.upload_object")
@patch("app.services.reporter_reports.fetch_report_by_ticket_hash")
def test_batch_single_file_uses_atomic_link_to_thread_rpc(
    fetch_mock: MagicMock,
    upload_mock: MagicMock,
    atomic_mock: MagicMock,
    client: TestClient,
) -> None:
    fetch_mock.return_value = _report_row(REPORT_B_ID, TICKET_B)
    atomic_mock.return_value = {
        "message_id": MESSAGE_ID,
        "attachment_id": "cccccccc-cccc-cccc-cccc-cccccccccccc",
        "attachment_uploaded_at": UPLOADED_AT,
        "file_type": "image/png",
    }
    _session_cookie(client)
    response = client.post(
        f"/api/reports/ticket/{TICKET_B}/attachments/batch",
        files=[("files", ("one.png", _minimal_png_bytes(), "image/png"))],
    )
    assert response.status_code == 201
    atomic_mock.assert_called_once()
    body = response.json()
    assert body["message_id"] == MESSAGE_ID
    assert len(body["attachments"]) == 1


@patch("app.services.reporter_reports.insert_attachment")
@patch("app.services.reporter_reports.insert_reporter_message")
@patch("app.services.reporter_reports.upload_object")
@patch("app.services.reporter_reports.fetch_report_by_ticket_hash")
def test_batch_multi_file_one_message_multiple_attachments(
    fetch_mock: MagicMock,
    upload_mock: MagicMock,
    insert_message_mock: MagicMock,
    insert_attachment_mock: MagicMock,
    client: TestClient,
) -> None:
    """N photos in one batch: one messages row, N attachment rows (not N atomic pairs)."""
    fetch_mock.return_value = _report_row(REPORT_B_ID, TICKET_B)
    insert_message_mock.return_value = {
        "id": MESSAGE_ID,
        "sender_type": "reporter",
        "content": "Photo attached",
        "created_at": UPLOADED_AT,
    }
    insert_attachment_mock.side_effect = [
        {
            "id": "11111111-1111-1111-1111-111111111111",
            "file_type": "image/png",
            "uploaded_at": UPLOADED_AT,
        },
        {
            "id": "22222222-2222-2222-2222-222222222222",
            "file_type": "image/png",
            "uploaded_at": UPLOADED_AT,
        },
    ]
    _session_cookie(client)
    png = _minimal_png_bytes()
    response = client.post(
        f"/api/reports/ticket/{TICKET_B}/attachments/batch",
        files=[
            ("files", ("one.png", png, "image/png")),
            ("files", ("two.png", png, "image/png")),
        ],
    )
    assert response.status_code == 201
    body = response.json()
    assert body["message_id"] == MESSAGE_ID
    assert len(body["attachments"]) == 2
    insert_message_mock.assert_called_once()
    assert insert_attachment_mock.call_count == 2
    for call in insert_attachment_mock.call_args_list:
        assert call.kwargs["message_id"] == MESSAGE_ID
        assert call.kwargs["report_id"] == REPORT_B_ID


def test_batch_service_rejects_empty_file_list(api_env: None) -> None:
    settings = get_settings()
    with pytest.raises(ValueError, match="At least one file"):
        upload_followup_attachments_batch(TICKET_B, [], settings=settings)
