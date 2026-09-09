"""PostgREST access for archived_reports and report deletion cascades."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from typing import Any

from app.exceptions.base import AppError


class ReportArchiveStoreError(AppError):
    """Report archive persistence layer failed."""


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


def _request(
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
        raise ReportArchiveStoreError(
            f"PostgREST {method} failed with HTTP {exc.code}.",
            context={"status": exc.code, "detail": detail},
        ) from exc
    except urllib.error.URLError as exc:
        raise ReportArchiveStoreError(
            f"PostgREST {method} could not connect.",
            context={"reason": str(exc.reason)},
        ) from exc
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        return [payload]
    return []


def insert_archived_report(
    *,
    supabase_url: str,
    service_role_key: str,
    row: dict[str, Any],
) -> dict[str, Any]:
    url = f"{supabase_url.rstrip('/')}/rest/v1/archived_reports"
    rows = _request(
        "POST",
        url,
        headers=_service_headers(service_role_key, prefer="return=representation"),
        body=row,
    )
    if not rows:
        raise ReportArchiveStoreError("Insert into archived_reports returned no row.")
    return rows[0]


def delete_rows_for_report(
    *,
    supabase_url: str,
    service_role_key: str,
    table: str,
    report_id: str,
) -> None:
    query = urllib.parse.urlencode({"report_id": f"eq.{report_id}"})
    url = f"{supabase_url.rstrip('/')}/rest/v1/{table}?{query}"
    _request(
        "DELETE",
        url,
        headers=_service_headers(service_role_key, prefer="return=minimal"),
    )


def delete_report_row(
    *,
    supabase_url: str,
    service_role_key: str,
    report_id: str,
) -> None:
    query = urllib.parse.urlencode({"id": f"eq.{report_id}"})
    url = f"{supabase_url.rstrip('/')}/rest/v1/reports?{query}"
    _request(
        "DELETE",
        url,
        headers=_service_headers(service_role_key, prefer="return=minimal"),
    )


def archive_timestamp() -> str:
    return datetime.now(tz=UTC).isoformat().replace("+00:00", "Z")
