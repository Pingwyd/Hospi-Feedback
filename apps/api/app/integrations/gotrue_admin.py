"""GoTrue admin client. Used by local seed now; Phase 2 admin-user flows reuse this."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from app.exceptions.gotrue import GoTrueAdminError


def _admin_headers(service_role_key: str) -> dict[str, str]:
    return {
        "apikey": service_role_key,
        "Authorization": f"Bearer {service_role_key}",
        "Content-Type": "application/json",
    }


def _request(
    method: str,
    url: str,
    *,
    service_role_key: str,
    body: dict[str, Any] | None = None,
) -> tuple[int, Any]:
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers=_admin_headers(service_role_key),
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            raw = response.read().decode("utf-8")
            payload = json.loads(raw) if raw else None
            return response.status, payload
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise GoTrueAdminError(
            f"GoTrue admin {method} {url} failed with HTTP {exc.code}.",
            context={"status": exc.code, "detail": detail},
        ) from exc
    except urllib.error.URLError as exc:
        raise GoTrueAdminError(
            f"GoTrue admin {method} {url} could not connect.",
            context={"reason": str(exc.reason)},
        ) from exc


def create_confirmed_email_user(
    *,
    supabase_url: str,
    service_role_key: str,
    email: str,
    password: str,
) -> str:
    """Create an Auth user with email already confirmed. Returns the user id."""
    url = f"{supabase_url.rstrip('/')}/auth/v1/admin/users"
    status, payload = _request(
        "POST",
        url,
        service_role_key=service_role_key,
        body={
            "email": email,
            "password": password,
            "email_confirm": True,
        },
    )
    missing_id = not isinstance(payload, dict) or not payload.get("id")
    if status not in (200, 201) or missing_id:
        raise GoTrueAdminError(
            "GoTrue admin create user did not return an id.",
            context={"status": status},
        )
    return str(payload["id"])


def find_user_id_by_email(
    *,
    supabase_url: str,
    service_role_key: str,
    email: str,
) -> str | None:
    query = urllib.parse.urlencode({"page": 1, "per_page": 200})
    url = f"{supabase_url.rstrip('/')}/auth/v1/admin/users?{query}"
    _status, payload = _request("GET", url, service_role_key=service_role_key)
    users = payload.get("users") if isinstance(payload, dict) else payload
    if not isinstance(users, list):
        return None
    needle = email.lower()
    for user in users:
        if isinstance(user, dict) and str(user.get("email") or "").lower() == needle:
            user_id = user.get("id")
            if user_id:
                return str(user_id)
    return None


def ensure_confirmed_email_user(
    *,
    supabase_url: str,
    service_role_key: str,
    email: str,
    password: str,
) -> str:
    existing = find_user_id_by_email(
        supabase_url=supabase_url,
        service_role_key=service_role_key,
        email=email,
    )
    if existing:
        return existing
    try:
        return create_confirmed_email_user(
            supabase_url=supabase_url,
            service_role_key=service_role_key,
            email=email,
            password=password,
        )
    except GoTrueAdminError as exc:
        # Race or duplicate: look up again before failing.
        existing = find_user_id_by_email(
            supabase_url=supabase_url,
            service_role_key=service_role_key,
            email=email,
        )
        if existing:
            return existing
        raise exc
