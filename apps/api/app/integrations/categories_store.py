"""PostgREST access for admin-managed categories."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from app.exceptions.base import AppError


class CategoriesStoreError(AppError):
    """Categories persistence layer failed."""


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
        raise CategoriesStoreError(
            f"PostgREST {method} failed with HTTP {exc.code}.",
            context={"status": exc.code, "detail": detail},
        ) from exc
    except urllib.error.URLError as exc:
        raise CategoriesStoreError(
            f"PostgREST {method} could not connect.",
            context={"reason": str(exc.reason)},
        ) from exc
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        return [payload]
    return []


def list_categories(
    *,
    supabase_url: str,
    service_role_key: str,
    active_only: bool = False,
) -> list[dict[str, Any]]:
    params: dict[str, str] = {
        "select": "id,name,active",
        "order": "name.asc",
    }
    if active_only:
        params["active"] = "eq.true"
    query = urllib.parse.urlencode(params)
    url = f"{supabase_url.rstrip('/')}/rest/v1/categories?{query}"
    return _request_json("GET", url, headers=_service_headers(service_role_key))


def insert_category(
    *,
    supabase_url: str,
    service_role_key: str,
    name: str,
) -> dict[str, Any]:
    url = f"{supabase_url.rstrip('/')}/rest/v1/categories"
    rows = _request_json(
        "POST",
        url,
        headers=_service_headers(service_role_key, prefer="return=representation"),
        body={"name": name, "active": True},
    )
    if not rows:
        raise CategoriesStoreError("Insert into categories returned no row.")
    return rows[0]


def patch_category(
    *,
    supabase_url: str,
    service_role_key: str,
    category_id: str,
    fields: dict[str, Any],
) -> dict[str, Any]:
    query = urllib.parse.urlencode({"id": f"eq.{category_id}"})
    url = f"{supabase_url.rstrip('/')}/rest/v1/categories?{query}"
    rows = _request_json(
        "PATCH",
        url,
        headers=_service_headers(service_role_key, prefer="return=representation"),
        body=fields,
    )
    if not rows:
        raise CategoriesStoreError("Patch on categories returned no row.")
    return rows[0]
