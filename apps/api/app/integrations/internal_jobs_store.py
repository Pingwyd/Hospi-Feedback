"""PostgREST queries for internal retention and duplicate-scan jobs."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from app.exceptions.base import AppError


class InternalJobsStoreError(AppError):
    """Internal jobs persistence layer failed."""


def _service_headers(service_role_key: str) -> dict[str, str]:
    return {
        "apikey": service_role_key,
        "Authorization": f"Bearer {service_role_key}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def _request_json(method: str, url: str, *, headers: dict[str, str]) -> list[Any]:
    req = urllib.request.Request(url, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            raw = response.read().decode("utf-8")
            payload = json.loads(raw) if raw else []
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise InternalJobsStoreError(
            f"PostgREST {method} failed with HTTP {exc.code}.",
            context={"status": exc.code, "detail": detail},
        ) from exc
    except urllib.error.URLError as exc:
        raise InternalJobsStoreError(
            f"PostgREST {method} could not connect.",
            context={"reason": str(exc.reason)},
        ) from exc
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        return [payload]
    return []


_REPORT_COLUMNS = (
    "id,ticket_code_hash,source,report_type,reported_member_name,"
    "reported_member_admin_id,description,incident_date,incident_location,"
    "severity,status,assigned_admin_id,publish_shoutout,is_public,"
    "possible_duplicate_of,created_at,updated_at"
)


def count_reports(
    *,
    supabase_url: str,
    service_role_key: str,
) -> int:
    url = f"{supabase_url.rstrip('/')}/rest/v1/reports?select=id"
    headers = _service_headers(service_role_key)
    headers["Prefer"] = "count=exact"
    req = urllib.request.Request(url, headers=headers, method="HEAD")
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            content_range = response.headers.get("Content-Range", "")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise InternalJobsStoreError(
            f"PostgREST HEAD failed with HTTP {exc.code}.",
            context={"status": exc.code, "detail": detail},
        ) from exc
    except urllib.error.URLError as exc:
        raise InternalJobsStoreError(
            "PostgREST HEAD could not connect.",
            context={"reason": str(exc.reason)},
        ) from exc
    if "/" not in content_range:
        return 0
    total = content_range.split("/")[-1].strip()
    return int(total) if total.isdigit() else 0


def list_reports_created_before(
    *,
    supabase_url: str,
    service_role_key: str,
    created_before_iso: str,
    limit: int = 500,
    offset: int = 0,
) -> list[dict[str, Any]]:
    query = urllib.parse.urlencode(
        {
            "created_at": f"lt.{created_before_iso}",
            "select": _REPORT_COLUMNS,
            "order": "created_at.asc",
            "limit": str(limit),
            "offset": str(offset),
        }
    )
    url = f"{supabase_url.rstrip('/')}/rest/v1/reports?{query}"
    rows = _request_json("GET", url, headers=_service_headers(service_role_key))
    return [row for row in rows if isinstance(row, dict)]


def list_reports_for_duplicate_scan(
    *,
    supabase_url: str,
    service_role_key: str,
    limit: int = 1000,
) -> list[dict[str, Any]]:
    query = urllib.parse.urlencode(
        {
            "possible_duplicate_of": "is.null",
            "reported_member_name": "not.is.null",
            "select": _REPORT_COLUMNS,
            "order": "created_at.asc",
            "limit": str(limit),
        }
    )
    url = f"{supabase_url.rstrip('/')}/rest/v1/reports?{query}"
    rows = _request_json("GET", url, headers=_service_headers(service_role_key))
    return [row for row in rows if isinstance(row, dict)]


def fetch_category_ids_for_reports(
    *,
    supabase_url: str,
    service_role_key: str,
    report_ids: list[str],
) -> dict[str, set[str]]:
    if not report_ids:
        return {}
    in_list = ",".join(report_ids)
    query = urllib.parse.urlencode(
        {
            "report_id": f"in.({in_list})",
            "select": "report_id,category_id",
        }
    )
    url = f"{supabase_url.rstrip('/')}/rest/v1/report_categories?{query}"
    rows = _request_json("GET", url, headers=_service_headers(service_role_key))
    mapping: dict[str, set[str]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        report_id = str(row.get("report_id") or "")
        category_id = str(row.get("category_id") or "")
        if report_id and category_id:
            mapping.setdefault(report_id, set()).add(category_id)
    return mapping
