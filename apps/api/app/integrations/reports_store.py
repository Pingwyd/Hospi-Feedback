"""PostgREST access for reporter-facing report and message rows."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from app.exceptions.base import AppError


class ReportsStoreError(AppError):
    """Report persistence layer failed."""


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
        raise ReportsStoreError(
            f"PostgREST {method} failed with HTTP {exc.code}.",
            context={"status": exc.code, "detail": detail},
        ) from exc
    except urllib.error.URLError as exc:
        raise ReportsStoreError(
            f"PostgREST {method} could not connect.",
            context={"reason": str(exc.reason)},
        ) from exc
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        return [payload]
    return []


def insert_report(
    *,
    supabase_url: str,
    service_role_key: str,
    row: dict[str, Any],
) -> dict[str, Any]:
    url = f"{supabase_url.rstrip('/')}/rest/v1/reports"
    rows = _request_json(
        "POST",
        url,
        headers=_service_headers(service_role_key, prefer="return=representation"),
        body=row,
    )
    if not rows:
        raise ReportsStoreError("Insert into reports returned no row.")
    return rows[0]


def insert_report_categories(
    *,
    supabase_url: str,
    service_role_key: str,
    report_id: str,
    category_ids: list[str],
) -> None:
    if not category_ids:
        return
    url = f"{supabase_url.rstrip('/')}/rest/v1/report_categories"
    body = [
        {"report_id": report_id, "category_id": category_id}
        for category_id in category_ids
    ]
    _request_json(
        "POST",
        url,
        headers=_service_headers(service_role_key, prefer="return=minimal"),
        body=body,
    )


def fetch_report_by_ticket_hash(
    *,
    supabase_url: str,
    service_role_key: str,
    ticket_code_hash: str,
) -> dict[str, Any] | None:
    query = urllib.parse.urlencode(
        {
            "ticket_code_hash": f"eq.{ticket_code_hash}",
            "select": (
                "id,status,report_type,description,reported_member_name,severity,"
                "created_at,updated_at"
            ),
        }
    )
    url = f"{supabase_url.rstrip('/')}/rest/v1/reports?{query}"
    rows = _request_json("GET", url, headers=_service_headers(service_role_key))
    return rows[0] if rows else None


def fetch_messages_for_report(
    *,
    supabase_url: str,
    service_role_key: str,
    report_id: str,
) -> list[dict[str, Any]]:
    query = urllib.parse.urlencode(
        {
            "report_id": f"eq.{report_id}",
            "select": "id,sender_type,content,created_at",
            "order": "created_at.asc",
        }
    )
    url = f"{supabase_url.rstrip('/')}/rest/v1/messages?{query}"
    return _request_json("GET", url, headers=_service_headers(service_role_key))


def insert_reporter_message(
    *,
    supabase_url: str,
    service_role_key: str,
    report_id: str,
    content: str,
) -> dict[str, Any]:
    url = f"{supabase_url.rstrip('/')}/rest/v1/messages"
    rows = _request_json(
        "POST",
        url,
        headers=_service_headers(service_role_key, prefer="return=representation"),
        body={
            "report_id": report_id,
            "sender_type": "reporter",
            "content": content,
        },
    )
    if not rows:
        raise ReportsStoreError("Insert into messages returned no row.")
    return rows[0]


def insert_attachment(
    *,
    supabase_url: str,
    service_role_key: str,
    report_id: str,
    storage_path: str,
    file_type: str,
) -> dict[str, Any]:
    url = f"{supabase_url.rstrip('/')}/rest/v1/attachments"
    rows = _request_json(
        "POST",
        url,
        headers=_service_headers(service_role_key, prefer="return=representation"),
        body={
            "report_id": report_id,
            "storage_path": storage_path,
            "file_type": file_type,
        },
    )
    if not rows:
        raise ReportsStoreError("Insert into attachments returned no row.")
    return rows[0]


def patch_report_status(
    *,
    supabase_url: str,
    service_role_key: str,
    report_id: str,
    status: str,
) -> dict[str, Any]:
    query = urllib.parse.urlencode({"id": f"eq.{report_id}"})
    url = f"{supabase_url.rstrip('/')}/rest/v1/reports?{query}"
    rows = _request_json(
        "PATCH",
        url,
        headers=_service_headers(service_role_key, prefer="return=representation"),
        body={"status": status},
    )
    if not rows:
        raise ReportsStoreError("Patch on reports returned no row.")
    return rows[0]


def count_attachments_for_report(
    *,
    supabase_url: str,
    service_role_key: str,
    report_id: str,
) -> int:
    query = urllib.parse.urlencode(
        {
            "report_id": f"eq.{report_id}",
            "select": "id",
        },
        doseq=True,
    )
    url = f"{supabase_url.rstrip('/')}/rest/v1/attachments?{query}"
    rows = _request_json("GET", url, headers=_service_headers(service_role_key))
    return len(rows)
