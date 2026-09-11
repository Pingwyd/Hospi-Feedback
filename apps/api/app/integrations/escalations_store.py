"""PostgREST access for escalation rows and export metadata."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from app.exceptions.base import AppError


class EscalationsStoreError(AppError):
    """Escalation persistence layer failed."""


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
        raise EscalationsStoreError(
            f"PostgREST {method} failed with HTTP {exc.code}.",
            context={"status": exc.code, "detail": detail},
        ) from exc
    except urllib.error.URLError as exc:
        raise EscalationsStoreError(
            f"PostgREST {method} could not connect.",
            context={"reason": str(exc.reason)},
        ) from exc
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        return [payload]
    return []


def list_expired_escalation_exports(
    *,
    supabase_url: str,
    service_role_key: str,
    expired_before_iso: str,
    limit: int = 500,
) -> list[dict[str, Any]]:
    query = urllib.parse.urlencode(
        {
            "export_retention_until": f"lt.{expired_before_iso}",
            "exported_file_path": "not.is.null",
            "select": "id,report_id,exported_file_path,export_retention_until",
            "order": "export_retention_until.asc",
            "limit": str(limit),
        }
    )
    url = f"{supabase_url.rstrip('/')}/rest/v1/escalations?{query}"
    return _request_json("GET", url, headers=_service_headers(service_role_key))


def clear_escalation_export(
    *,
    supabase_url: str,
    service_role_key: str,
    escalation_id: str,
) -> dict[str, Any]:
    return patch_escalation_fields(
        supabase_url=supabase_url,
        service_role_key=service_role_key,
        escalation_id=escalation_id,
        fields={
            "exported_file_path": None,
            "export_retention_until": None,
        },
    )


def fetch_escalation_by_id(
    *,
    supabase_url: str,
    service_role_key: str,
    escalation_id: str,
) -> dict[str, Any] | None:
    query = urllib.parse.urlencode(
        {
            "id": f"eq.{escalation_id}",
            "select": "id,report_id,exported_file_path,export_retention_until",
        }
    )
    url = f"{supabase_url.rstrip('/')}/rest/v1/escalations?{query}"
    rows = _request_json("GET", url, headers=_service_headers(service_role_key))
    return rows[0] if rows else None


def patch_escalation_fields(
    *,
    supabase_url: str,
    service_role_key: str,
    escalation_id: str,
    fields: dict[str, Any],
) -> dict[str, Any]:
    query = urllib.parse.urlencode({"id": f"eq.{escalation_id}"})
    url = f"{supabase_url.rstrip('/')}/rest/v1/escalations?{query}"
    rows = _request_json(
        "PATCH",
        url,
        headers=_service_headers(service_role_key, prefer="return=representation"),
        body=fields,
    )
    if not rows:
        raise EscalationsStoreError("Patch on escalations returned no row.")
    return rows[0]
