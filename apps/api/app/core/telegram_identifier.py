"""One-way Telegram chat id hashing for rate limiting only."""

from __future__ import annotations

import hashlib
import hmac


def hash_telegram_identifier(chat_id: int | str, *, pepper: str) -> str:
    """Return hex SHA-256 of chat id with server-shared pepper."""
    if not pepper:
        raise ValueError("Telegram identifier pepper must not be empty.")
    material = f"{chat_id}:{pepper}".encode()
    return hashlib.sha256(material).hexdigest()


def identifier_hash_matches(
    chat_id: int | str, *, pepper: str, stored_hash_hex: str
) -> bool:
    submitted = bytes.fromhex(hash_telegram_identifier(chat_id, pepper=pepper))
    try:
        stored = bytes.fromhex(stored_hash_hex)
    except ValueError:
        return False
    return hmac.compare_digest(submitted, stored)
