from unittest.mock import MagicMock, patch

import pytest
from app.core.settings import get_settings
from app.exceptions.reports import ReportClosedError, ReportNotFoundError
from app.main import create_app
from app.services.reporter_reports import CreateReportInput, create_report
from fastapi.testclient import TestClient
from tests.conftest import FIXTURE_ACCESS_CODE

REPORT_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
CREATED_AT = "2026-09-03T12:00:00+00:00"
TICKET_CODE = "ABCD2345"


@pytest.fixture
def client(api_env: None) -> TestClient:
    return TestClient(create_app())


def _session_cookie(client: TestClient) -> None:
    response = client.post(
        "/api/access/verify",
        json={"access_code": FIXTURE_ACCESS_CODE},
    )
    assert response.status_code == 200


def _inserted_report(ticket_hash: str) -> dict:
    return {
        "id": REPORT_ID,
        "status": "new",
        "created_at": CREATED_AT,
        "ticket_code_hash": ticket_hash,
    }


@patch("app.services.reporter_reports.generate_ticket_code", return_value=TICKET_CODE)
@patch("app.services.reporter_reports.insert_report")
def test_create_report_returns_plaintext_once(
    insert_mock: MagicMock,
    _generate_mock: MagicMock,
    api_env: None,
) -> None:
    from app.core.ticket_code import hash_ticket_code

    insert_mock.return_value = _inserted_report(hash_ticket_code(TICKET_CODE))
    settings = get_settings()
    result = create_report(
        CreateReportInput(report_type="complaint", description="Test report body."),
        settings=settings,
    )
    assert result.ticket_code == TICKET_CODE
    stored = insert_mock.call_args.kwargs["row"]
    assert stored["ticket_code_hash"] == hash_ticket_code(TICKET_CODE)
    assert "ticket_code" not in stored


@patch("app.api.routes.reports.get_ticket_status")
@patch("app.api.routes.reports.create_report")
def test_submit_then_fetch_by_ticket(
    create_mock: MagicMock,
    fetch_mock: MagicMock,
    client: TestClient,
) -> None:
    from app.services.reporter_reports import CreateReportResult

    create_mock.return_value = CreateReportResult(
        ticket_code=TICKET_CODE,
        status="new",
        created_at=CREATED_AT,
    )
    fetch_mock.return_value = {
        "status": "new",
        "report_type": "complaint",
        "description": "Test report body.",
        "reported_member_name": None,
        "severity": None,
        "created_at": CREATED_AT,
        "updated_at": CREATED_AT,
        "messages": [],
    }
    _session_cookie(client)
    submit = client.post(
        "/api/reports",
        json={"report_type": "complaint", "description": "Test report body."},
    )
    assert submit.status_code == 201
    assert submit.json()["ticket_code"] == TICKET_CODE

    fetch = client.get(f"/api/reports/ticket/{TICKET_CODE}")
    assert fetch.status_code == 200
    assert fetch.json()["status"] == "new"


@patch("app.api.routes.reports.post_reporter_message")
@patch("app.api.routes.reports.get_ticket_status")
@patch("app.api.routes.reports.create_report")
def test_wrong_ticket_code_returns_404(
    _create_mock: MagicMock,
    fetch_mock: MagicMock,
    _message_mock: MagicMock,
    client: TestClient,
) -> None:
    fetch_mock.side_effect = ReportNotFoundError("Report not found.")
    _session_cookie(client)
    response = client.get("/api/reports/ticket/ZZZZZZZZ")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


@patch("app.services.reporter_reports.insert_reporter_message")
@patch("app.services.reporter_reports.fetch_messages_for_report", return_value=[])
@patch("app.services.reporter_reports.fetch_report_by_ticket_hash")
@patch("app.services.reporter_reports.generate_ticket_code", return_value=TICKET_CODE)
@patch("app.services.reporter_reports.insert_report")
def test_message_rejected_after_close(
    insert_report_mock: MagicMock,
    _generate_mock: MagicMock,
    fetch_report_mock: MagicMock,
    _fetch_messages_mock: MagicMock,
    insert_message_mock: MagicMock,
    client: TestClient,
    api_env: None,
) -> None:
    from app.core.ticket_code import hash_ticket_code

    ticket_hash = hash_ticket_code(TICKET_CODE)
    insert_report_mock.return_value = _inserted_report(ticket_hash)
    fetch_report_mock.side_effect = [
        {
            "id": REPORT_ID,
            "status": "new",
            "report_type": "complaint",
            "description": "Test report body.",
            "reported_member_name": None,
            "severity": None,
            "created_at": CREATED_AT,
            "updated_at": CREATED_AT,
        },
        {
            "id": REPORT_ID,
            "status": "closed",
            "report_type": "complaint",
            "description": "Test report body.",
            "reported_member_name": None,
            "severity": None,
            "created_at": CREATED_AT,
            "updated_at": CREATED_AT,
        },
    ]
    insert_message_mock.return_value = {
        "id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        "sender_type": "reporter",
        "content": "Follow-up question.",
        "created_at": CREATED_AT,
    }

    _session_cookie(client)
    submit = client.post(
        "/api/reports",
        json={"report_type": "complaint", "description": "Test report body."},
    )
    assert submit.status_code == 201

    first_message = client.post(
        f"/api/reports/ticket/{TICKET_CODE}/message",
        json={"content": "Follow-up question."},
    )
    assert first_message.status_code == 201

    # TEST-ONLY close simulation: production will use Phase 4 admin PATCH. Real curl
    # demos call patch_report_status via service_role PostgREST (see script below).
    closed_message = client.post(
        f"/api/reports/ticket/{TICKET_CODE}/message",
        json={"content": "Should be rejected."},
    )
    assert closed_message.status_code == 409
    assert closed_message.json()["error"]["code"] == "conflict"


def test_post_reporter_message_raises_when_closed(api_env: None) -> None:
    from app.services.reporter_reports import post_reporter_message

    with patch(
        "app.services.reporter_reports.fetch_report_by_ticket_hash",
        return_value={"id": REPORT_ID, "status": "closed"},
    ):
        settings = get_settings()
        with pytest.raises(ReportClosedError, match="Report is closed"):
            post_reporter_message(
                TICKET_CODE,
                "hello",
                settings=settings,
            )
