"""Tests for in-memory access session helpers."""

from datetime import UTC, datetime, timedelta

from bot.sessions import (
    access_token,
    clear_access_session,
    has_valid_access_session,
    store_access_session,
)


def test_store_and_read_valid_session() -> None:
    user_data: dict = {}
    expires = (
        (datetime.now(tz=UTC) + timedelta(hours=1)).isoformat().replace("+00:00", "Z")
    )
    store_access_session(user_data, token="token-value", expires_at=expires)
    assert has_valid_access_session(user_data)
    assert access_token(user_data) == "token-value"


def test_expired_session_is_cleared() -> None:
    user_data: dict = {}
    expires = (
        (datetime.now(tz=UTC) - timedelta(minutes=1)).isoformat().replace("+00:00", "Z")
    )
    store_access_session(user_data, token="token-value", expires_at=expires)
    assert access_token(user_data) is None
    assert not has_valid_access_session(user_data)


def test_clear_access_session() -> None:
    user_data: dict = {"access_token": "x", "access_expires_at": "y"}
    clear_access_session(user_data)
    assert user_data == {}
