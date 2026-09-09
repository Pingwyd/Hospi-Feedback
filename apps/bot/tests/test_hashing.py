"""Tests for one-way Telegram identifier hashing."""

from bot.hashing import hash_telegram_identifier


def test_hash_is_stable_and_hex() -> None:
    first = hash_telegram_identifier(123456789, pepper="test-pepper")
    second = hash_telegram_identifier(123456789, pepper="test-pepper")
    assert first == second
    assert len(first) == 64
    assert all(ch in "0123456789abcdef" for ch in first)


def test_hash_changes_with_pepper() -> None:
    a = hash_telegram_identifier(42, pepper="pepper-a")
    b = hash_telegram_identifier(42, pepper="pepper-b")
    assert a != b
