"""GoTrue user auth: password login and MFA."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

from app.exceptions.gotrue import GoTrueAdminError


@dataclass(frozen=True)
class GoTrueSession:
    access_token: str
    refresh_token: str
    expires_in: int
    user_id: str


def _auth_headers(*, api_key: str, access_token: str | None = None) -> dict[str, str]:
    bearer = access_token or api_key
    return {
        "apikey": api_key,
        "Authorization": f"Bearer {bearer}",
        "Content-Type": "application/json",
    }


def _request(
    method: str,
    url: str,
    *,
    headers: dict[str, str],
    body: dict[str, Any] | None = None,
) -> tuple[int, Any]:
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            raw = response.read().decode("utf-8")
            payload = json.loads(raw) if raw else None
            return response.status, payload
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise GoTrueAdminError(
            f"GoTrue {method} {url} failed with HTTP {exc.code}.",
            context={"status": exc.code, "detail": detail},
        ) from exc
    except urllib.error.URLError as exc:
        raise GoTrueAdminError(
            f"GoTrue {method} {url} could not connect.",
            context={"reason": str(exc.reason)},
        ) from exc


def sign_in_with_password(
    *,
    supabase_url: str,
    anon_key: str,
    email: str,
    password: str,
) -> GoTrueSession:
    query = urllib.parse.urlencode({"grant_type": "password"})
    url = f"{supabase_url.rstrip('/')}/auth/v1/token?{query}"
    status, payload = _request(
        "POST",
        url,
        headers=_auth_headers(api_key=anon_key),
        body={"email": email, "password": password},
    )
    if status != 200 or not isinstance(payload, dict):
        raise GoTrueAdminError(
            "GoTrue password sign-in did not return a session.",
            context={"status": status},
        )
    access_token = payload.get("access_token")
    refresh_token = payload.get("refresh_token")
    user = payload.get("user")
    user_id = user.get("id") if isinstance(user, dict) else None
    if not access_token or not refresh_token or not user_id:
        raise GoTrueAdminError(
            "GoTrue password sign-in response was incomplete.",
            context={"status": status},
        )
    expires_in = int(payload.get("expires_in") or 3600)
    return GoTrueSession(
        access_token=str(access_token),
        refresh_token=str(refresh_token),
        expires_in=expires_in,
        user_id=str(user_id),
    )


def list_user_mfa_factors(
    *,
    supabase_url: str,
    service_role_key: str,
    user_id: str,
) -> list[dict[str, Any]]:
    url = f"{supabase_url.rstrip('/')}/auth/v1/admin/users/{user_id}/factors"
    status, payload = _request(
        "GET",
        url,
        headers=_auth_headers(api_key=service_role_key),
    )
    if status != 200 or not isinstance(payload, list):
        raise GoTrueAdminError(
            "GoTrue admin list factors did not return a list.",
            context={"status": status},
        )
    return [item for item in payload if isinstance(item, dict)]


def create_mfa_challenge(
    *,
    supabase_url: str,
    anon_key: str,
    factor_id: str,
    access_token: str,
) -> str:
    url = f"{supabase_url.rstrip('/')}/auth/v1/factors/{factor_id}/challenge"
    status, payload = _request(
        "POST",
        url,
        headers=_auth_headers(api_key=anon_key, access_token=access_token),
        body={},
    )
    challenge_id = payload.get("id") if isinstance(payload, dict) else None
    if status != 200 or not challenge_id:
        raise GoTrueAdminError(
            "GoTrue MFA challenge did not return an id.",
            context={"status": status},
        )
    return str(challenge_id)


def verify_mfa_challenge(
    *,
    supabase_url: str,
    anon_key: str,
    factor_id: str,
    access_token: str,
    challenge_id: str,
    code: str,
) -> GoTrueSession:
    url = f"{supabase_url.rstrip('/')}/auth/v1/factors/{factor_id}/verify"
    status, payload = _request(
        "POST",
        url,
        headers=_auth_headers(api_key=anon_key, access_token=access_token),
        body={"challenge_id": challenge_id, "code": code},
    )
    if status != 200 or not isinstance(payload, dict):
        raise GoTrueAdminError(
            "GoTrue MFA verify did not return a session.",
            context={"status": status},
        )
    access_token_out = payload.get("access_token")
    refresh_token = payload.get("refresh_token")
    user = payload.get("user")
    user_id = user.get("id") if isinstance(user, dict) else None
    if not access_token_out or not refresh_token or not user_id:
        raise GoTrueAdminError(
            "GoTrue MFA verify response was incomplete.",
            context={"status": status},
        )
    expires_in = int(payload.get("expires_in") or 3600)
    return GoTrueSession(
        access_token=str(access_token_out),
        refresh_token=str(refresh_token),
        expires_in=expires_in,
        user_id=str(user_id),
    )
