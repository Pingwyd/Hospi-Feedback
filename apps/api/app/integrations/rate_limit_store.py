"""PostgREST access for rate_limit_entries counters."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from typing import Any

from app.exceptions.base import AppError


class RateLimitStoreError(AppError):
    """Rate limit persistence failed."""


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
        raise RateLimitStoreError(
            f"PostgREST {method} failed with HTTP {exc.code}.",
            context={"status": exc.code, "detail": detail},
        ) from exc
    except urllib.error.URLError as exc:
        raise RateLimitStoreError(
            f"PostgREST {method} could not connect.",
            context={"reason": str(exc.reason)},
        ) from exc
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        return [payload]
    return []


def fetch_entry_for_window(
    *,
    supabase_url: str,
    service_role_key: str,
    channel: str,
    identifier_hash: str,
    window_start: datetime,
) -> dict[str, Any] | None:
    window_iso = window_start.astimezone(UTC).isoformat().replace("+00:00", "Z")
    query = urllib.parse.urlencode(
        {
            "channel": f"eq.{channel}",
            "identifier_hash": f"eq.{identifier_hash}",
            "window_start": f"eq.{window_iso}",
            "select": "id,request_count",
        }
    )
    url = f"{supabase_url.rstrip('/')}/rest/v1/rate_limit_entries?{query}"
    rows = _request_json("GET", url, headers=_service_headers(service_role_key))
    return rows[0] if rows else None


def insert_entry(
    *,
    supabase_url: str,
    service_role_key: str,
    channel: str,
    identifier_hash: str,
    window_start: datetime,
) -> dict[str, Any]:
    window_iso = window_start.astimezone(UTC).isoformat().replace("+00:00", "Z")
    url = f"{supabase_url.rstrip('/')}/rest/v1/rate_limit_entries"
    rows = _request_json(
        "POST",
        url,
        headers=_service_headers(service_role_key, prefer="return=representation"),
        body={
            "channel": channel,
            "identifier_hash": identifier_hash,
            "window_start": window_iso,
            "request_count": 1,
        },
    )
    if not rows:
        raise RateLimitStoreError("Insert into rate_limit_entries returned no row.")
    return rows[0]


def increment_entry(
    *,
    supabase_url: str,
    service_role_key: str,
    entry_id: str,
    request_count: int,
) -> dict[str, Any]:
    query = urllib.parse.urlencode({"id": f"eq.{entry_id}"})
    url = f"{supabase_url.rstrip('/')}/rest/v1/rate_limit_entries?{query}"
    rows = _request_json(
        "PATCH",
        url,
        headers=_service_headers(service_role_key, prefer="return=representation"),
        body={"request_count": request_count},
    )
    if not rows:
        raise RateLimitStoreError("Patch on rate_limit_entries returned no row.")
    return rows[0]
