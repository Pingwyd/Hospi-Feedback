"""PostgREST access for admin user management."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from app.exceptions.base import AppError


class AdminManagementStoreError(AppError):
    """Admin management persistence layer failed."""


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
        raise AdminManagementStoreError(
            f"PostgREST {method} failed with HTTP {exc.code}.",
            context={"status": exc.code, "detail": detail},
        ) from exc
    except urllib.error.URLError as exc:
        raise AdminManagementStoreError(
            f"PostgREST {method} could not connect.",
            context={"reason": str(exc.reason)},
        ) from exc
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        return [payload]
    return []


def list_admins(
    *,
    supabase_url: str,
    service_role_key: str,
) -> list[dict[str, Any]]:
    query = urllib.parse.urlencode(
        {
            "select": (
                "id,full_name,role,subunit,aliases,active,created_at,"
                "admin_permissions(permission)"
            ),
            "order": "full_name.asc",
        }
    )
    url = f"{supabase_url.rstrip('/')}/rest/v1/admins?{query}"
    return _request_json("GET", url, headers=_service_headers(service_role_key))


def insert_admin_row(
    *,
    supabase_url: str,
    service_role_key: str,
    row: dict[str, Any],
) -> dict[str, Any]:
    url = f"{supabase_url.rstrip('/')}/rest/v1/admins"
    rows = _request_json(
        "POST",
        url,
        headers=_service_headers(service_role_key, prefer="return=representation"),
        body=row,
    )
    if not rows:
        raise AdminManagementStoreError("Insert into admins returned no row.")
    return rows[0]


def patch_admin_row(
    *,
    supabase_url: str,
    service_role_key: str,
    admin_id: str,
    fields: dict[str, Any],
) -> dict[str, Any]:
    query = urllib.parse.urlencode({"id": f"eq.{admin_id}"})
    url = f"{supabase_url.rstrip('/')}/rest/v1/admins?{query}"
    rows = _request_json(
        "PATCH",
        url,
        headers=_service_headers(service_role_key, prefer="return=representation"),
        body=fields,
    )
    if not rows:
        raise AdminManagementStoreError("Patch on admins returned no row.")
    return rows[0]


def delete_permissions_for_admin(
    *,
    supabase_url: str,
    service_role_key: str,
    admin_id: str,
) -> None:
    query = urllib.parse.urlencode({"admin_id": f"eq.{admin_id}"})
    url = f"{supabase_url.rstrip('/')}/rest/v1/admin_permissions?{query}"
    _request_json(
        "DELETE",
        url,
        headers=_service_headers(service_role_key, prefer="return=minimal"),
    )


def insert_admin_permissions(
    *,
    supabase_url: str,
    service_role_key: str,
    admin_id: str,
    permissions: list[str],
) -> None:
    if not permissions:
        return
    url = f"{supabase_url.rstrip('/')}/rest/v1/admin_permissions"
    body = [{"admin_id": admin_id, "permission": perm} for perm in permissions]
    _request_json(
        "POST",
        url,
        headers=_service_headers(service_role_key, prefer="return=minimal"),
        body=body,
    )
