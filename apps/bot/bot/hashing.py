"""One-way Telegram chat id hashing for API rate limiting."""

from __future__ import annotations

import hashlib


def hash_telegram_identifier(chat_id: int | str, *, pepper: str) -> str:
    if not pepper:
        raise ValueError("Telegram identifier pepper must not be empty.")
    material = f"{chat_id}:{pepper}".encode()
    return hashlib.sha256(material).hexdigest()
