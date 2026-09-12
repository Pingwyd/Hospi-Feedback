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
    message_id: str | None = None,
) -> dict[str, Any]:
    url = f"{supabase_url.rstrip('/')}/rest/v1/attachments"
    body: dict[str, Any] = {
        "report_id": report_id,
        "storage_path": storage_path,
        "file_type": file_type,
    }
    if message_id is not None:
        body["message_id"] = message_id
    rows = _request_json(
        "POST",
        url,
        headers=_service_headers(service_role_key, prefer="return=representation"),
        body=body,
    )
    if not rows:
        raise ReportsStoreError("Insert into attachments returned no row.")
    return rows[0]


def insert_followup_attachment_atomic(
    *,
    supabase_url: str,
    service_role_key: str,
    report_id: str,
    content: str,
    storage_path: str,
    file_type: str,
) -> dict[str, Any]:
    """Message + attachment in one DB transaction via Postgres RPC."""
    url = f"{supabase_url.rstrip('/')}/rest/v1/rpc/create_reporter_followup_attachment"
    rows = _request_json(
        "POST",
        url,
        headers=_service_headers(service_role_key),
        body={
            "p_report_id": report_id,
            "p_content": content,
            "p_storage_path": storage_path,
            "p_file_type": file_type,
        },
    )
    if not rows:
        raise ReportsStoreError(
            "RPC create_reporter_followup_attachment returned no row.",
        )
    return rows[0]


def fetch_attachments_for_report(
    *,
    supabase_url: str,
    service_role_key: str,
    report_id: str,
) -> list[dict[str, Any]]:
    query = urllib.parse.urlencode(
        {
            "report_id": f"eq.{report_id}",
            "select": "id,report_id,message_id,storage_path,file_type,uploaded_at",
            "order": "uploaded_at.asc",
        }
    )
    url = f"{supabase_url.rstrip('/')}/rest/v1/attachments?{query}"
    return _request_json("GET", url, headers=_service_headers(service_role_key))


def fetch_attachment_by_id(
    *,
    supabase_url: str,
    service_role_key: str,
    attachment_id: str,
) -> dict[str, Any] | None:
    query = urllib.parse.urlencode(
        {
            "id": f"eq.{attachment_id}",
            "select": "id,report_id,message_id,storage_path,file_type,uploaded_at",
        }
    )
    url = f"{supabase_url.rstrip('/')}/rest/v1/attachments?{query}"
    rows = _request_json("GET", url, headers=_service_headers(service_role_key))
    return rows[0] if rows else None


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


_ADMIN_REPORT_COLUMNS = (
    "id,ticket_code_hash,source,report_type,reported_member_name,"
    "reported_member_admin_id,description,incident_date,incident_location,"
    "severity,status,assigned_admin_id,publish_shoutout,is_public,"
    "possible_duplicate_of,created_at,updated_at"
)


def fetch_report_by_id(
    *,
    supabase_url: str,
    service_role_key: str,
    report_id: str,
) -> dict[str, Any] | None:
    query = urllib.parse.urlencode(
        {
            "id": f"eq.{report_id}",
            "select": _ADMIN_REPORT_COLUMNS,
        }
    )
    url = f"{supabase_url.rstrip('/')}/rest/v1/reports?{query}"
    rows = _request_json("GET", url, headers=_service_headers(service_role_key))
    return rows[0] if rows else None


def list_reports(
    *,
    supabase_url: str,
    service_role_key: str,
    status: str | None = None,
    keyword: str | None = None,
    created_from: str | None = None,
    created_to: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict[str, Any]]:
    params: dict[str, str] = {
        "select": _ADMIN_REPORT_COLUMNS,
        "order": "created_at.desc",
        "limit": str(limit),
        "offset": str(offset),
    }
    if status:
        params["status"] = f"eq.{status}"
    if keyword:
        params["or"] = (
            f"(description.ilike.*{keyword}*,reported_member_name.ilike.*{keyword}*)"
        )
    if created_from and created_to:
        params["and"] = f"(created_at.gte.{created_from},created_at.lte.{created_to})"
    elif created_from:
        params["created_at"] = f"gte.{created_from}"
    elif created_to:
        params["created_at"] = f"lte.{created_to}"
    query = urllib.parse.urlencode(params)
    url = f"{supabase_url.rstrip('/')}/rest/v1/reports?{query}"
    return _request_json("GET", url, headers=_service_headers(service_role_key))


def fetch_category_names_for_report(
    *,
    supabase_url: str,
    service_role_key: str,
    report_id: str,
) -> list[str]:
    query = urllib.parse.urlencode(
        {
            "report_id": f"eq.{report_id}",
            "select": "categories(name)",
        }
    )
    url = f"{supabase_url.rstrip('/')}/rest/v1/report_categories?{query}"
    rows = _request_json("GET", url, headers=_service_headers(service_role_key))
    names: list[str] = []
    for row in rows:
        category = row.get("categories")
        if isinstance(category, dict):
            name = category.get("name")
            if isinstance(name, str) and name.strip():
                names.append(name.strip())
    return names


def patch_report_fields(
    *,
    supabase_url: str,
    service_role_key: str,
    report_id: str,
    fields: dict[str, Any],
) -> dict[str, Any]:
    query = urllib.parse.urlencode({"id": f"eq.{report_id}"})
    url = f"{supabase_url.rstrip('/')}/rest/v1/reports?{query}"
    rows = _request_json(
        "PATCH",
        url,
        headers=_service_headers(service_role_key, prefer="return=representation"),
        body=fields,
    )
    if not rows:
        raise ReportsStoreError("Patch on reports returned no row.")
    return rows[0]


def insert_admin_message(
    *,
    supabase_url: str,
    service_role_key: str,
    report_id: str,
    sender_admin_id: str,
    content: str,
) -> dict[str, Any]:
    url = f"{supabase_url.rstrip('/')}/rest/v1/messages"
    rows = _request_json(
        "POST",
        url,
        headers=_service_headers(service_role_key, prefer="return=representation"),
        body={
            "report_id": report_id,
            "sender_type": "admin",
            "sender_admin_id": sender_admin_id,
            "content": content,
        },
    )
    if not rows:
        raise ReportsStoreError("Insert into messages returned no row.")
    return rows[0]


def insert_internal_note(
    *,
    supabase_url: str,
    service_role_key: str,
    report_id: str,
    admin_id: str,
    content: str,
) -> dict[str, Any]:
    url = f"{supabase_url.rstrip('/')}/rest/v1/internal_notes"
    rows = _request_json(
        "POST",
        url,
        headers=_service_headers(service_role_key, prefer="return=representation"),
        body={
            "report_id": report_id,
            "admin_id": admin_id,
            "content": content,
        },
    )
    if not rows:
        raise ReportsStoreError("Insert into internal_notes returned no row.")
    return rows[0]


def fetch_internal_notes_for_report(
    *,
    supabase_url: str,
    service_role_key: str,
    report_id: str,
) -> list[dict[str, Any]]:
    query = urllib.parse.urlencode(
        {
            "report_id": f"eq.{report_id}",
            "select": "id,admin_id,content,created_at",
            "order": "created_at.asc",
        }
    )
    url = f"{supabase_url.rstrip('/')}/rest/v1/internal_notes?{query}"
    return _request_json("GET", url, headers=_service_headers(service_role_key))


def insert_escalation(
    *,
    supabase_url: str,
    service_role_key: str,
    report_id: str,
    escalation_contact_id: str,
    escalated_by_admin_id: str,
) -> dict[str, Any]:
    url = f"{supabase_url.rstrip('/')}/rest/v1/escalations"
    rows = _request_json(
        "POST",
        url,
        headers=_service_headers(service_role_key, prefer="return=representation"),
        body={
            "report_id": report_id,
            "escalation_contact_id": escalation_contact_id,
            "escalated_by_admin_id": escalated_by_admin_id,
        },
    )
    if not rows:
        raise ReportsStoreError("Insert into escalations returned no row.")
    return rows[0]
