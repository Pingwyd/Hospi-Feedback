"""PostgREST access for dashboard system alerts."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from app.exceptions.base import AppError


class SystemAlertsStoreError(AppError):
    """System alerts persistence failed."""


def _service_headers(
    service_role_key: str, *, prefer: str | None = None
) -> dict[str, str]:
    headers = {
        "apikey": service_role_key,
        "Authorization": f"Bearer {service_role_key}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    if prefer:
        headers["Prefer"] = prefer
    return headers


def _request_json(
    method: str,
    url: str,
    *,
    headers: dict[str, str],
    body: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            raw = response.read().decode("utf-8")
            payload = json.loads(raw) if raw else []
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemAlertsStoreError(
            f"PostgREST {method} failed with HTTP {exc.code}.",
            context={"status": exc.code, "detail": detail},
        ) from exc
    except urllib.error.URLError as exc:
        raise SystemAlertsStoreError(
            f"PostgREST {method} could not connect.",
            context={"reason": str(exc.reason)},
        ) from exc
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        return [payload]
    return []


def insert_system_alert(
    *,
    supabase_url: str,
    service_role_key: str,
    alert_type: str,
    message: str,
) -> dict[str, Any]:
    url = f"{supabase_url.rstrip('/')}/rest/v1/system_alerts"
    rows = _request_json(
        "POST",
        url,
        headers=_service_headers(service_role_key, prefer="return=representation"),
        body={"alert_type": alert_type, "message": message},
    )
    if not rows:
        raise SystemAlertsStoreError("Insert into system_alerts returned no row.")
    return rows[0]


def list_active_system_alerts(
    *,
    supabase_url: str,
    service_role_key: str,
    limit: int = 20,
) -> list[dict[str, Any]]:
    query = urllib.parse.urlencode(
        {
            "dismissed_at": "is.null",
            "select": "id,alert_type,message,created_at",
            "order": "created_at.desc",
            "limit": str(limit),
        }
    )
    url = f"{supabase_url.rstrip('/')}/rest/v1/system_alerts?{query}"
    return _request_json("GET", url, headers=_service_headers(service_role_key))
