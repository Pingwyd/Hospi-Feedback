"""Tests for reporter ticket-scoped WebSocket live updates."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import jwt
import pytest
from app.core.access_session import (
    ACCESS_TOKEN_ALG,
    ACCESS_TOKEN_TYP,
    issue_access_token,
)
from app.core.ticket_code import hash_ticket_code
from app.exceptions.reports import ReportNotFoundError
from app.main import create_app
from app.services.reporter_ws import (
    ReporterWsConnection,
    broadcast_reporter_event,
    reporter_ws_manager,
)
from fastapi.testclient import TestClient
from tests.conftest import FIXTURE_ACCESS_CODE, FIXTURE_ACCESS_JWT_SECRET

REPORT_ID_A = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
REPORT_ID_B = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
TICKET_CODE_A = "ABCD2345"
TICKET_CODE_B = "WXYZ6789"
CREATED_AT = "2026-09-03T12:00:00+00:00"


@pytest.fixture
def client(api_env: None) -> TestClient:
    return TestClient(create_app())


def _session_cookie(client: TestClient) -> None:
    response = client.post(
        "/api/access/verify",
        json={"access_code": FIXTURE_ACCESS_CODE},
    )
    assert response.status_code == 200


def _access_token() -> str:
    token, _expires = issue_access_token(
        secret=FIXTURE_ACCESS_JWT_SECRET,
        ttl_seconds=3600,
    )
    return token


def _report_row(report_id: str, ticket_code: str) -> dict:
    return {
        "id": report_id,
        "status": "new",
        "created_at": CREATED_AT,
        "ticket_code_hash": hash_ticket_code(ticket_code),
        "report_type": "complaint",
        "description": "Test",
        "updated_at": CREATED_AT,
    }


def test_ws_bootstrap_returns_token_with_valid_cookie(client: TestClient) -> None:
    _session_cookie(client)
    response = client.get("/api/access/ws-bootstrap")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["access_token"], str)
    assert body["access_token"]
    assert body["expires_at"].endswith("Z")


def test_ws_bootstrap_requires_session(client: TestClient) -> None:
    response = client.get("/api/access/ws-bootstrap")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_broadcast_to_report_is_ticket_scoped() -> None:
    ws_a = AsyncMock()
    ws_b = AsyncMock()
    token = _access_token()
    conn_a = ReporterWsConnection(
        websocket=ws_a,
        report_id=REPORT_ID_A,
        session_id="sid-a",
        token=token,
        secret=FIXTURE_ACCESS_JWT_SECRET,
    )
    conn_b = ReporterWsConnection(
        websocket=ws_b,
        report_id=REPORT_ID_B,
        session_id="sid-b",
        token=token,
        secret=FIXTURE_ACCESS_JWT_SECRET,
    )
    await reporter_ws_manager.register(conn_a)
    await reporter_ws_manager.register(conn_b)
    try:
        await broadcast_reporter_event(
            REPORT_ID_A,
            "new_message",
            {
                "message_id": "msg-admin-1",
                "sender_type": "admin",
                "created_at": CREATED_AT,
            },
        )
        ws_a.send_text.assert_awaited_once()
        ws_b.send_text.assert_not_awaited()
    finally:
        reporter_ws_manager.unregister(conn_a)
        reporter_ws_manager.unregister(conn_b)


@patch("app.api.routes.reporter_websocket._load_report_by_ticket_code")
def test_reporter_ws_receives_admin_message_signal(
    load_report_mock: MagicMock,
    client: TestClient,
) -> None:
    import asyncio

    load_report_mock.return_value = _report_row(REPORT_ID_A, TICKET_CODE_A)
    token = _access_token()
    with client.websocket_connect(
        f"/api/reports/ticket/{TICKET_CODE_A}/ws?access_token={token}",
    ) as ws:
        asyncio.run(
            broadcast_reporter_event(
                REPORT_ID_A,
                "new_message",
                {
                    "message_id": "msg-admin-1",
                    "sender_type": "admin",
                    "created_at": CREATED_AT,
                },
            ),
        )
        event = ws.receive_json()
        assert event["event"] == "new_message"
        assert event["payload"]["message_id"] == "msg-admin-1"
        assert event["payload"]["sender_type"] == "admin"


@patch("app.api.routes.reporter_websocket._load_report_by_ticket_code")
def test_reporter_ws_rejects_unknown_ticket(
    load_report_mock: MagicMock,
    client: TestClient,
) -> None:
    load_report_mock.side_effect = ReportNotFoundError("Report not found.")
    token = _access_token()
    with pytest.raises(Exception):
        with client.websocket_connect(
            f"/api/reports/ticket/{TICKET_CODE_A}/ws?access_token={token}",
        ):
            pass


def test_reporter_ws_rejects_expired_token(client: TestClient) -> None:
    expired_payload = {
        "iat": datetime.now(tz=UTC) - timedelta(hours=25),
        "exp": datetime.now(tz=UTC) - timedelta(hours=1),
        "sid": "00000000-0000-0000-0000-000000000001",
        "typ": ACCESS_TOKEN_TYP,
    }
    token = jwt.encode(
        expired_payload,
        FIXTURE_ACCESS_JWT_SECRET,
        algorithm=ACCESS_TOKEN_ALG,
    )
    with pytest.raises(Exception):
        with client.websocket_connect(
            f"/api/reports/ticket/{TICKET_CODE_A}/ws?access_token={token}",
        ):
            pass


@pytest.mark.asyncio
@patch("app.services.admin_reports.send_reporter_message")
@patch("app.services.admin_reports.broadcast_admin_event", new_callable=AsyncMock)
async def test_admin_reply_broadcasts_to_reporter_channel(
    admin_broadcast_mock: AsyncMock,
    send_message_mock: MagicMock,
) -> None:
    from app.core.admin_auth import AdminContext
    from app.core.settings import get_settings
    from app.services.admin_reports import send_reporter_message_and_notify

    send_message_mock.return_value = {
        "id": "msg-admin-99",
        "sender_type": "admin",
        "content": "We are reviewing this.",
        "created_at": CREATED_AT,
    }
    admin = AdminContext(
        id="admin-1",
        full_name="Admin",
        role="staff",
        subunit=None,
        aliases=(),
        permissions=frozenset({"respond"}),
    )
    with patch(
        "app.services.admin_reports.broadcast_reporter_event",
        new_callable=AsyncMock,
    ) as reporter_broadcast_mock:
        await send_reporter_message_and_notify(
            report_id=REPORT_ID_A,
            content="We are reviewing this.",
            admin=admin,
            settings=get_settings(),
        )
        reporter_broadcast_mock.assert_awaited_once_with(
            REPORT_ID_A,
            "new_message",
            {
                "message_id": "msg-admin-99",
                "sender_type": "admin",
                "created_at": CREATED_AT,
            },
        )
