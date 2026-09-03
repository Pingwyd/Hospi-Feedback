"""PostgREST reads for admin rows. Writes stay in later phases."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

from app.exceptions.base import AppError


class SupabaseRestError(AppError):
    """PostgREST request failed."""


@dataclass(frozen=True)
class AdminRecord:
    id: str
    full_name: str
    role: str | None
    subunit: str | None
    aliases: tuple[str, ...]
    active: bool


def _service_headers(service_role_key: str) -> dict[str, str]:
    return {
        "apikey": service_role_key,
        "Authorization": f"Bearer {service_role_key}",
        "Accept": "application/json",
    }


def _get_json(url: str, *, headers: dict[str, str]) -> list[dict[str, Any]]:
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            raw = response.read().decode("utf-8")
            payload = json.loads(raw) if raw else []
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SupabaseRestError(
            f"PostgREST GET failed with HTTP {exc.code}.",
            context={"status": exc.code, "detail": detail},
        ) from exc
    except urllib.error.URLError as exc:
        raise SupabaseRestError(
            "PostgREST GET could not connect.",
            context={"reason": str(exc.reason)},
        ) from exc
    if not isinstance(payload, list):
        raise SupabaseRestError("PostgREST GET did not return a JSON array.")
    return [row for row in payload if isinstance(row, dict)]


def fetch_active_admin(
    *,
    supabase_url: str,
    service_role_key: str,
    admin_id: str,
) -> AdminRecord | None:
    query = urllib.parse.urlencode(
        {
            "id": f"eq.{admin_id}",
            "active": "eq.true",
            "select": "id,full_name,role,subunit,aliases,active",
        }
    )
    url = f"{supabase_url.rstrip('/')}/rest/v1/admins?{query}"
    rows = _get_json(url, headers=_service_headers(service_role_key))
    if not rows:
        return None
    row = rows[0]
    aliases_raw = row.get("aliases") or []
    aliases = tuple(str(item) for item in aliases_raw if item)
    return AdminRecord(
        id=str(row["id"]),
        full_name=str(row.get("full_name") or ""),
        role=str(row["role"]) if row.get("role") else None,
        subunit=str(row["subunit"]) if row.get("subunit") else None,
        aliases=aliases,
        active=bool(row.get("active", True)),
    )


def fetch_admin_permissions(
    *,
    supabase_url: str,
    service_role_key: str,
    admin_id: str,
) -> frozenset[str]:
    query = urllib.parse.urlencode(
        {
            "admin_id": f"eq.{admin_id}",
            "select": "permission",
        }
    )
    url = f"{supabase_url.rstrip('/')}/rest/v1/admin_permissions?{query}"
    rows = _get_json(url, headers=_service_headers(service_role_key))
    return frozenset(str(row["permission"]) for row in rows if row.get("permission"))
