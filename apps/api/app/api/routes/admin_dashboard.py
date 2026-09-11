"""Dashboard stats and admin WebSocket routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect

from app.api.deps import require_permission
from app.core.admin_auth import (
    AdminContext,
    load_admin_context,
    verify_supabase_access_token,
)
from app.core.settings import Settings, get_settings
from app.exceptions.auth import AdminSessionError
from app.services.admin_dashboard import get_dashboard_stats
from app.services.admin_ws import admin_ws_manager

router = APIRouter(tags=["admin-dashboard"])


@router.get("/api/admin/dashboard/stats")
def get_stats(
    admin: AdminContext = Depends(require_permission("view")),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    return {"data": get_dashboard_stats(admin=admin, settings=settings)}


@router.websocket("/api/admin/ws")
async def admin_websocket(
    websocket: WebSocket,
    access_token: str = Query(...),
) -> None:
    settings = get_settings()
    try:
        claims = verify_supabase_access_token(
            access_token,
            settings=settings,
        )
        admin = load_admin_context(str(claims["sub"]), settings=settings)
    except AdminSessionError:
        await websocket.close(code=4401)
        return
    if "view" not in admin.permissions:
        await websocket.close(code=4403)
        return

    await admin_ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        admin_ws_manager.disconnect(websocket)
