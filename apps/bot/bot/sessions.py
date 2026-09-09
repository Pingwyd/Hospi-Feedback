"""In-memory access session helpers (user_data only, never persisted)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from bot.constants import SESSION_EXPIRES_KEY, SESSION_TOKEN_KEY


def store_access_session(
    user_data: dict[str, Any], *, token: str, expires_at: str
) -> None:
    user_data[SESSION_TOKEN_KEY] = token
    user_data[SESSION_EXPIRES_KEY] = expires_at


def clear_access_session(user_data: dict[str, Any]) -> None:
    user_data.pop(SESSION_TOKEN_KEY, None)
    user_data.pop(SESSION_EXPIRES_KEY, None)


def access_token(user_data: dict[str, Any]) -> str | None:
    token = user_data.get(SESSION_TOKEN_KEY)
    if not isinstance(token, str) or not token:
        return None
    expires_at = user_data.get(SESSION_EXPIRES_KEY)
    if isinstance(expires_at, str) and expires_at:
        try:
            expiry = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
        except ValueError:
            return None
        if expiry <= datetime.now(tz=UTC):
            clear_access_session(user_data)
            return None
    return token


def has_valid_access_session(user_data: dict[str, Any]) -> bool:
    return access_token(user_data) is not None
