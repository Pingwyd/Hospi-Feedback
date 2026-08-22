"""Minimal PostgREST client for local seed. FastAPI will use its own client later."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


class PostgrestError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        status: int | None = None,
        detail: str = "",
    ) -> None:
        super().__init__(message)
        self.status = status
        self.detail = detail


def _headers(service_role_key: str, *, prefer: str | None = None) -> dict[str, str]:
    headers = {
        "apikey": service_role_key,
        "Authorization": f"Bearer {service_role_key}",
        "Content-Type": "application/json",
    }
    if prefer:
        headers["Prefer"] = prefer
    return headers


def rest_get(
    *,
    supabase_url: str,
    service_role_key: str,
    table: str,
    query: dict[str, str],
) -> list[dict[str, Any]]:
    qs = urllib.parse.urlencode(query)
    url = f"{supabase_url.rstrip('/')}/rest/v1/{table}?{qs}"
    req = urllib.request.Request(
        url,
        headers=_headers(service_role_key),
        method="GET",
    )
    return _read_json_list(req)


def rest_insert(
    *,
    supabase_url: str,
    service_role_key: str,
    table: str,
    row: dict[str, Any],
) -> dict[str, Any]:
    url = f"{supabase_url.rstrip('/')}/rest/v1/{table}"
    req = urllib.request.Request(
        url,
        data=json.dumps(row).encode("utf-8"),
        headers=_headers(service_role_key, prefer="return=representation"),
        method="POST",
    )
    rows = _read_json_list(req)
    if not rows:
        raise PostgrestError(f"Insert into {table} returned no row.")
    return rows[0]


def _read_json_list(req: urllib.request.Request) -> list[dict[str, Any]]:
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            raw = response.read().decode("utf-8")
            payload = json.loads(raw) if raw else []
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise PostgrestError(
            f"PostgREST {req.get_method()} failed with HTTP {exc.code}.",
            status=exc.code,
            detail=detail,
        ) from exc
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        return [payload]
    raise PostgrestError("PostgREST returned an unexpected JSON shape.")
