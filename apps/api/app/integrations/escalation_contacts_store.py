"""PostgREST access for escalation contacts."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from app.exceptions.base import AppError


class EscalationContactsStoreError(AppError):
    """Escalation contacts persistence layer failed."""


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
        raise EscalationContactsStoreError(
            f"PostgREST {method} failed with HTTP {exc.code}.",
            context={"status": exc.code, "detail": detail},
        ) from exc
    except urllib.error.URLError as exc:
        raise EscalationContactsStoreError(
            f"PostgREST {method} could not connect.",
            context={"reason": str(exc.reason)},
        ) from exc
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        return [payload]
    return []


def list_escalation_contacts(
    *,
    supabase_url: str,
    service_role_key: str,
    active_only: bool = False,
) -> list[dict[str, Any]]:
    params: dict[str, str] = {
        "select": "id,name,role_label,contact_email,contact_phone,active",
        "order": "name.asc",
    }
    if active_only:
        params["active"] = "eq.true"
    query = urllib.parse.urlencode(params)
    url = f"{supabase_url.rstrip('/')}/rest/v1/escalation_contacts?{query}"
    return _request_json("GET", url, headers=_service_headers(service_role_key))


def insert_escalation_contact(
    *,
    supabase_url: str,
    service_role_key: str,
    row: dict[str, Any],
) -> dict[str, Any]:
    url = f"{supabase_url.rstrip('/')}/rest/v1/escalation_contacts"
    rows = _request_json(
        "POST",
        url,
        headers=_service_headers(service_role_key, prefer="return=representation"),
        body=row,
    )
    if not rows:
        raise EscalationContactsStoreError(
            "Insert into escalation_contacts returned no row."
        )
    return rows[0]


def patch_escalation_contact(
    *,
    supabase_url: str,
    service_role_key: str,
    contact_id: str,
    fields: dict[str, Any],
) -> dict[str, Any]:
    query = urllib.parse.urlencode({"id": f"eq.{contact_id}"})
    url = f"{supabase_url.rstrip('/')}/rest/v1/escalation_contacts?{query}"
    rows = _request_json(
        "PATCH",
        url,
        headers=_service_headers(service_role_key, prefer="return=representation"),
        body=fields,
    )
    if not rows:
        raise EscalationContactsStoreError(
            "Patch on escalation_contacts returned no row."
        )
    return rows[0]
