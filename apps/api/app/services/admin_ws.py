"""In-memory admin WebSocket fan-out for dashboard live updates."""

from __future__ import annotations

import json
from typing import Any

from fastapi import WebSocket


class AdminWsManager:
    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self._connections.discard(websocket)

    async def broadcast(self, event: str, payload: dict[str, Any]) -> None:
        message = json.dumps({"event": event, "payload": payload})
        stale: list[WebSocket] = []
        for websocket in self._connections:
            try:
                await websocket.send_text(message)
            except Exception:
                stale.append(websocket)
        for websocket in stale:
            self.disconnect(websocket)


admin_ws_manager = AdminWsManager()


async def broadcast_admin_event(event: str, payload: dict[str, Any]) -> None:
    await admin_ws_manager.broadcast(event, payload)
