"""HTTP client for the Hospi Feedback API."""

from __future__ import annotations

from typing import Any, Literal

import httpx

ReportType = Literal["complaint", "suggestion", "recognition"]
Severity = Literal["low", "medium", "high"]


class ApiClientError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


class HospiApiClient:
    def __init__(
        self,
        *,
        base_url: str,
        bot_service_secret: str = "",
        timeout: float = 30.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._bot_service_secret = bot_service_secret.strip()
        self._timeout = timeout

    async def verify_access_code(self, access_code: str) -> dict[str, Any]:
        return await self._request(
            "POST",
            "/api/access/verify",
            json={"access_code": access_code},
            headers={"X-Session-Transport": "bearer"},
        )

    async def check_rate_limit(
        self, *, token: str, identifier_hash: str
    ) -> dict[str, Any]:
        return await self._request(
            "POST",
            "/api/rate-limit/check",
            json={"channel": "telegram", "identifier_hash": identifier_hash},
            token=token,
        )

    async def link_telegram_account(
        self,
        *,
        one_time_code: str,
        telegram_chat_id: str,
    ) -> dict[str, Any]:
        return await self._request(
            "POST",
            "/api/admin/telegram/link",
            json={
                "one_time_code": one_time_code,
                "telegram_chat_id": telegram_chat_id,
            },
            headers={"X-Bot-Service-Secret": self._bot_service_secret},
        )

    async def create_report(
        self,
        *,
        token: str,
        report_type: ReportType,
        description: str,
        reported_member_name: str | None = None,
        severity: Severity | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "report_type": report_type,
            "description": description,
            "source": "telegram",
        }
        if reported_member_name:
            payload["reported_member_name"] = reported_member_name
        if severity:
            payload["severity"] = severity
        return await self._request(
            "POST",
            "/api/reports",
            json=payload,
            token=token,
        )

    async def get_ticket_status(
        self, *, token: str, ticket_code: str
    ) -> dict[str, Any]:
        return await self._request(
            "GET",
            f"/api/reports/ticket/{ticket_code}",
            token=token,
        )

    async def post_ticket_message(
        self, *, token: str, ticket_code: str, content: str
    ) -> dict[str, Any]:
        return await self._request(
            "POST",
            f"/api/reports/ticket/{ticket_code}/message",
            json={"content": content},
            token=token,
        )

    async def upload_attachment(
        self,
        *,
        token: str,
        ticket_code: str,
        filename: str,
        content_type: str,
        data: bytes,
    ) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                f"{self._base_url}/api/reports/ticket/{ticket_code}/attachments",
                headers=headers,
                files={"file": (filename, data, content_type)},
            )
        return self._parse_response(response)

    async def _request(
        self,
        method: str,
        path: str,
        *,
        token: str | None = None,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        request_headers = dict(headers or {})
        if token:
            request_headers["Authorization"] = f"Bearer {token}"
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.request(
                method,
                f"{self._base_url}{path}",
                json=json,
                headers=request_headers,
            )
        return self._parse_response(response)

    @staticmethod
    def _parse_response(response: httpx.Response) -> dict[str, Any]:
        payload: Any = {}
        if response.content:
            payload = response.json()
        if response.is_success:
            if isinstance(payload, dict):
                return payload
            return {"data": payload}
        if isinstance(payload, dict) and "error" in payload:
            error = payload["error"]
            raise ApiClientError(
                response.status_code,
                str(error.get("code", "error")),
                str(error.get("message", "Request failed.")),
            )
        raise ApiClientError(
            response.status_code,
            "error",
            f"Request failed with status {response.status_code}.",
        )
