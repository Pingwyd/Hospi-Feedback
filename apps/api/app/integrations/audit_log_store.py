"""PostgREST access for admin audit_log rows."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from app.exceptions.base import AppError


class AuditLogStoreError(AppError):
    """Audit log persistence layer failed."""


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
    body: list[dict[str, Any]] | dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            raw = response.read().decode("utf-8")
            payload = json.loads(raw) if raw else []
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise AuditLogStoreError(
            f"PostgREST {method} failed with HTTP {exc.code}.",
            context={"status": exc.code, "detail": detail},
        ) from exc
    except urllib.error.URLError as exc:
        raise AuditLogStoreError(
            f"PostgREST {method} could not connect.",
            context={"reason": str(exc.reason)},
        ) from exc
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        return [payload]
    return []


def insert_audit_log_row(
    *,
    supabase_url: str,
    service_role_key: str,
    admin_id: str,
    report_id: str | None,
    action: str,
    detail: dict[str, Any] | None,
) -> dict[str, Any]:
    url = f"{supabase_url.rstrip('/')}/rest/v1/audit_log"
    row: dict[str, Any] = {
        "admin_id": admin_id,
        "report_id": report_id,
        "action": action,
    }
    if detail is not None:
        row["detail"] = detail
    rows = _request_json(
        "POST",
        url,
        headers=_service_headers(service_role_key, prefer="return=representation"),
        body=row,
    )
    if not rows:
        raise AuditLogStoreError("Insert into audit_log returned no row.")
    return rows[0]


def list_audit_log_entries(
    *,
    supabase_url: str,
    service_role_key: str,
    report_id: str | None = None,
    admin_id: str | None = None,
    action: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict[str, Any]]:
    params: dict[str, str] = {
        "select": "id,admin_id,report_id,action,detail,created_at",
        "order": "created_at.desc",
        "limit": str(limit),
        "offset": str(offset),
    }
    if report_id:
        params["report_id"] = f"eq.{report_id}"
    if admin_id:
        params["admin_id"] = f"eq.{admin_id}"
    if action:
        params["action"] = f"eq.{action}"
    query = urllib.parse.urlencode(params)
    url = f"{supabase_url.rstrip('/')}/rest/v1/audit_log?{query}"
    return _request_json("GET", url, headers=_service_headers(service_role_key))
