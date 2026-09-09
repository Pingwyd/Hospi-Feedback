"""PostgREST access for telegram_link_codes and admin Telegram chat ids."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from typing import Any

from app.exceptions.base import AppError


class TelegramAdminStoreError(AppError):
    """Telegram admin persistence failed."""


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
        raise TelegramAdminStoreError(
            f"PostgREST {method} failed with HTTP {exc.code}.",
            context={"status": exc.code, "detail": detail},
        ) from exc
    except urllib.error.URLError as exc:
        raise TelegramAdminStoreError(
            f"PostgREST {method} could not connect.",
            context={"reason": str(exc.reason)},
        ) from exc
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        return [payload]
    return []


def _store_kwargs(supabase_url: str, service_role_key: str) -> dict[str, str]:
    return {
        "supabase_url": supabase_url,
        "service_role_key": service_role_key,
    }


def invalidate_unused_codes_for_admin(
    *,
    supabase_url: str,
    service_role_key: str,
    admin_id: str,
    used_at: datetime,
) -> None:
    used_iso = used_at.astimezone(UTC).isoformat().replace("+00:00", "Z")
    query = urllib.parse.urlencode(
        {
            "admin_id": f"eq.{admin_id}",
            "used_at": "is.null",
        }
    )
    url = f"{supabase_url.rstrip('/')}/rest/v1/telegram_link_codes?{query}"
    _request_json(
        "PATCH",
        url,
        headers=_service_headers(service_role_key, prefer="return=minimal"),
        body={"used_at": used_iso},
    )


def insert_link_code(
    *,
    supabase_url: str,
    service_role_key: str,
    admin_id: str,
    code_hash: str,
    expires_at: datetime,
) -> dict[str, Any]:
    expires_iso = expires_at.astimezone(UTC).isoformat().replace("+00:00", "Z")
    url = f"{supabase_url.rstrip('/')}/rest/v1/telegram_link_codes"
    rows = _request_json(
        "POST",
        url,
        headers=_service_headers(service_role_key, prefer="return=representation"),
        body={
            "admin_id": admin_id,
            "code_hash": code_hash,
            "expires_at": expires_iso,
        },
    )
    if not rows:
        raise TelegramAdminStoreError(
            "Insert into telegram_link_codes returned no row."
        )
    return rows[0]


def fetch_active_link_code_by_hash(
    *,
    supabase_url: str,
    service_role_key: str,
    code_hash: str,
) -> dict[str, Any] | None:
    query = urllib.parse.urlencode(
        {
            "code_hash": f"eq.{code_hash}",
            "used_at": "is.null",
            "select": "id,admin_id,expires_at",
        }
    )
    url = f"{supabase_url.rstrip('/')}/rest/v1/telegram_link_codes?{query}"
    rows = _request_json("GET", url, headers=_service_headers(service_role_key))
    return rows[0] if rows else None


def mark_link_code_used(
    *,
    supabase_url: str,
    service_role_key: str,
    link_code_id: str,
    used_at: datetime,
) -> None:
    used_iso = used_at.astimezone(UTC).isoformat().replace("+00:00", "Z")
    query = urllib.parse.urlencode({"id": f"eq.{link_code_id}"})
    url = f"{supabase_url.rstrip('/')}/rest/v1/telegram_link_codes?{query}"
    _request_json(
        "PATCH",
        url,
        headers=_service_headers(service_role_key, prefer="return=minimal"),
        body={"used_at": used_iso},
    )


def fetch_linked_admin_rows(
    *,
    supabase_url: str,
    service_role_key: str,
) -> list[dict[str, str]]:
    query = urllib.parse.urlencode(
        {
            "active": "eq.true",
            "telegram_chat_id_encrypted": "not.is.null",
            "select": "id,telegram_chat_id_encrypted",
        }
    )
    url = f"{supabase_url.rstrip('/')}/rest/v1/admins?{query}"
    rows = _request_json("GET", url, headers=_service_headers(service_role_key))
    linked: list[dict[str, str]] = []
    for row in rows:
        encrypted = row.get("telegram_chat_id_encrypted")
        admin_id = row.get("id")
        if encrypted and admin_id:
            linked.append(
                {
                    "id": str(admin_id),
                    "telegram_chat_id_encrypted": str(encrypted),
                }
            )
    return linked


def update_admin_telegram_chat_id(
    *,
    supabase_url: str,
    service_role_key: str,
    admin_id: str,
    telegram_chat_id_encrypted: str,
) -> None:
    query = urllib.parse.urlencode({"id": f"eq.{admin_id}"})
    url = f"{supabase_url.rstrip('/')}/rest/v1/admins?{query}"
    _request_json(
        "PATCH",
        url,
        headers=_service_headers(service_role_key, prefer="return=minimal"),
        body={"telegram_chat_id_encrypted": telegram_chat_id_encrypted},
    )
