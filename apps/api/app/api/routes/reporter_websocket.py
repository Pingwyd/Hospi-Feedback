"""Reporter ticket-scoped WebSocket for live status page updates."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from fastapi import (
    APIRouter,
    Cookie,
    Depends,
    Header,
    Query,
    WebSocket,
    WebSocketDisconnect,
)
from pydantic import BaseModel

from app.core.access_session import verify_access_token
from app.core.settings import Settings, get_settings
from app.exceptions.access import AccessDeniedError
from app.exceptions.reports import ReportNotFoundError
from app.services.reporter_reports import _load_report_by_ticket_code
from app.services.reporter_ws import ReporterWsConnection, reporter_ws_manager

router = APIRouter(tags=["reports"])


def _bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, _, value = authorization.partition(" ")
    if scheme.lower() != "bearer" or not value:
        return None
    return value.strip() or None


class WsBootstrapResponse(BaseModel):
    access_token: str
    expires_at: str


@router.get("/api/access/ws-bootstrap", response_model=WsBootstrapResponse)
def ws_bootstrap(
    settings: Annotated[Settings, Depends(get_settings)],
    authorization: Annotated[str | None, Header()] = None,
    hospi_access_session: Annotated[str | None, Cookie()] = None,
) -> WsBootstrapResponse:
    token = _bearer_token(authorization) or hospi_access_session
    if not token:
        raise AccessDeniedError("Access session required.")
    claims = verify_access_token(token, secret=settings.access_code_jwt_secret)
    exp = claims.get("exp")
    if not isinstance(exp, (int, float)):
        raise AccessDeniedError("Access session invalid.")
    expires_at = datetime.fromtimestamp(exp, tz=UTC).isoformat().replace("+00:00", "Z")
    return WsBootstrapResponse(access_token=token, expires_at=expires_at)


@router.websocket("/api/reports/ticket/{ticket_code}/ws")
async def reporter_ticket_websocket(
    websocket: WebSocket,
    ticket_code: str,
    access_token: str = Query(...),
) -> None:
    settings = get_settings()
    client_host = websocket.client.host if websocket.client else "unknown"
    rate_key = client_host

    try:
        claims = verify_access_token(
            access_token,
            secret=settings.access_code_jwt_secret,
        )
    except AccessDeniedError:
        if not reporter_ws_manager.failed_connect_allowed(rate_key):
            await websocket.close(code=4429)
            return
        reporter_ws_manager.record_failed_connect(rate_key)
        await websocket.close(code=4401)
        return

    session_id = str(claims.get("sid") or "")
    if session_id:
        rate_key = session_id

    try:
        report = _load_report_by_ticket_code(ticket_code, settings=settings)
    except ReportNotFoundError:
        if not reporter_ws_manager.failed_connect_allowed(rate_key):
            await websocket.close(code=4429)
            return
        reporter_ws_manager.record_failed_connect(rate_key)
        await websocket.close(code=4404)
        return

    report_id = str(report["id"])
    if not reporter_ws_manager.can_accept(report_id=report_id, session_id=session_id):
        await websocket.close(code=4429)
        return

    await websocket.accept()
    connection = ReporterWsConnection(
        websocket=websocket,
        report_id=report_id,
        session_id=session_id,
        token=access_token,
        secret=settings.access_code_jwt_secret,
    )
    await reporter_ws_manager.register(connection)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        reporter_ws_manager.unregister(connection)
    except Exception:
        reporter_ws_manager.unregister(connection)
        raise
