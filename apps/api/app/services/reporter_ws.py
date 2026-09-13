"""Ticket-scoped reporter WebSocket fan-out for live status page updates."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any

from fastapi import WebSocket

from app.core.access_session import verify_access_token
from app.exceptions.access import AccessDeniedError

logger = logging.getLogger(__name__)

SESSION_VALIDATION_INTERVAL_SECONDS = 60
FAILED_CONNECT_WINDOW_SECONDS = 60


@dataclass
class ReporterWsConnection:
    websocket: WebSocket
    report_id: str
    session_id: str
    token: str
    secret: str


@dataclass
class _FailedConnectTracker:
    """Counts rejected handshakes only; successful connects are not limited here."""

    max_failures_per_window: int
    _events: dict[str, deque[float]] = field(default_factory=lambda: defaultdict(deque))

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        window = self._events[key]
        while window and now - window[0] > FAILED_CONNECT_WINDOW_SECONDS:
            window.popleft()
        return len(window) < self.max_failures_per_window

    def record_failure(self, key: str) -> None:
        self._events[key].append(time.monotonic())


class ReporterWsManager:
    def __init__(
        self,
        *,
        max_per_ticket: int = 3,
        max_per_session: int = 5,
        max_total: int = 100,
        max_failed_connects_per_window: int = 10,
    ) -> None:
        self._max_per_ticket = max_per_ticket
        self._max_per_session = max_per_session
        self._max_total = max_total
        self._failed_connects = _FailedConnectTracker(
            max_failures_per_window=max_failed_connects_per_window,
        )
        self._by_report: dict[str, list[ReporterWsConnection]] = defaultdict(list)
        self._all: list[ReporterWsConnection] = []

    def failed_connect_allowed(self, rate_key: str) -> bool:
        return self._failed_connects.allow(rate_key)

    def record_failed_connect(self, rate_key: str) -> None:
        self._failed_connects.record_failure(rate_key)

    def _count_for_session(self, session_id: str) -> int:
        return sum(1 for conn in self._all if conn.session_id == session_id)

    def can_accept(
        self,
        *,
        report_id: str,
        session_id: str,
    ) -> bool:
        if len(self._all) >= self._max_total:
            return False
        if len(self._by_report[report_id]) >= self._max_per_ticket:
            return False
        if self._count_for_session(session_id) >= self._max_per_session:
            return False
        return True

    async def register(self, connection: ReporterWsConnection) -> None:
        self._all.append(connection)
        self._by_report[connection.report_id].append(connection)

    def unregister(self, connection: ReporterWsConnection) -> None:
        self._all = [conn for conn in self._all if conn is not connection]
        report_connections = self._by_report.get(connection.report_id)
        if report_connections is not None:
            self._by_report[connection.report_id] = [
                conn for conn in report_connections if conn is not connection
            ]
            if not self._by_report[connection.report_id]:
                self._by_report.pop(connection.report_id, None)

    async def disconnect(self, connection: ReporterWsConnection) -> None:
        self.unregister(connection)
        try:
            await connection.websocket.close()
        except Exception:
            pass

    async def broadcast_to_report(
        self,
        report_id: str,
        event: str,
        payload: dict[str, Any],
    ) -> None:
        message = json.dumps({"event": event, "payload": payload})
        targets = list(self._by_report.get(report_id, ()))
        stale: list[ReporterWsConnection] = []
        for connection in targets:
            try:
                verify_access_token(connection.token, secret=connection.secret)
            except AccessDeniedError:
                stale.append(connection)
                continue
            try:
                await connection.websocket.send_text(message)
            except Exception:
                stale.append(connection)
        for connection in stale:
            await self._close_session(connection, reason="session_expired")

    async def _close_session(
        self,
        connection: ReporterWsConnection,
        *,
        reason: str,
    ) -> None:
        self.unregister(connection)
        try:
            await connection.websocket.send_text(
                json.dumps({"event": reason, "payload": {}}),
            )
        except Exception:
            pass
        try:
            await connection.websocket.close(code=4401)
        except Exception:
            pass

    async def validate_sessions_once(self) -> None:
        expired: list[ReporterWsConnection] = []
        for connection in list(self._all):
            try:
                verify_access_token(connection.token, secret=connection.secret)
            except AccessDeniedError:
                expired.append(connection)
        for connection in expired:
            await self._close_session(connection, reason="session_expired")

    async def run_session_validation_loop(
        self,
        interval_seconds: int = SESSION_VALIDATION_INTERVAL_SECONDS,
    ) -> None:
        while True:
            await asyncio.sleep(interval_seconds)
            try:
                await self.validate_sessions_once()
            except Exception:
                logger.exception("reporter_ws_session_validation_failed")


reporter_ws_manager = ReporterWsManager()


async def broadcast_reporter_event(
    report_id: str,
    event: str,
    payload: dict[str, Any],
) -> None:
    await reporter_ws_manager.broadcast_to_report(report_id, event, payload)
