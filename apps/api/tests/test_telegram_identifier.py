"""Tests for Telegram identifier hashing in the API."""

from app.core.telegram_identifier import (
    hash_telegram_identifier,
    identifier_hash_matches,
)


def test_hash_is_deterministic() -> None:
    first = hash_telegram_identifier("12345", pepper="pepper")
    second = hash_telegram_identifier("12345", pepper="pepper")
    assert first == second
    assert len(first) == 64


def test_identifier_hash_matches() -> None:
    digest = hash_telegram_identifier(999, pepper="pepper")
    assert identifier_hash_matches(999, pepper="pepper", stored_hash_hex=digest)
    assert not identifier_hash_matches(998, pepper="pepper", stored_hash_hex=digest)
