"""Telegram admin linking and chat-id resolution for bot-facing routes."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.core.crypto import (
    ENV_KEY_NAME,
    decrypt_telegram_chat_id,
    encrypt_telegram_chat_id,
)
from app.core.link_code import (
    generate_link_code,
    hash_link_code,
    is_valid_link_code_format,
    normalize_link_code,
)
from app.core.settings import Settings
from app.exceptions.telegram_admin import (
    TelegramAdminNotLinkedError,
    TelegramLinkRejectedError,
)
from app.integrations.telegram_admin_store import (
    fetch_active_link_code_by_hash,
    fetch_linked_admin_rows,
    insert_link_code,
    invalidate_unused_codes_for_admin,
    mark_link_code_used,
    update_admin_telegram_chat_id,
)

TELEGRAM_CHAT_ID_PATTERN = re.compile(r"^-?\d+$")


@dataclass(frozen=True)
class GeneratedLinkCode:
    link_code: str
    expires_at: datetime


def _store_kwargs(settings: Settings) -> dict[str, str]:
    return {
        "supabase_url": settings.supabase_url,
        "service_role_key": settings.supabase_service_role_key,
    }


def _crypto_environ(settings: Settings) -> dict[str, str]:
    """Map Settings fields to the env names crypto helpers expect."""
    return {ENV_KEY_NAME: settings.telegram_chat_id_encryption_key}


def _normalize_chat_id(chat_id: str | int) -> str:
    raw = str(chat_id).strip()
    if not TELEGRAM_CHAT_ID_PATTERN.fullmatch(raw):
        raise TelegramLinkRejectedError("Invalid Telegram chat id.")
    return raw


def _parse_expires_at(raw: object) -> datetime:
    if not isinstance(raw, str):
        raise TelegramLinkRejectedError("Invalid or expired link code.")
    return datetime.fromisoformat(raw.replace("Z", "+00:00"))


def generate_telegram_link_code(
    *,
    admin_id: str,
    settings: Settings,
) -> GeneratedLinkCode:
    now = datetime.now(tz=UTC)
    invalidate_unused_codes_for_admin(
        **_store_kwargs(settings),
        admin_id=admin_id,
        used_at=now,
    )
    plaintext = generate_link_code()
    expires_at = now + timedelta(seconds=settings.telegram_link_code_ttl_seconds)
    insert_link_code(
        **_store_kwargs(settings),
        admin_id=admin_id,
        code_hash=hash_link_code(plaintext),
        expires_at=expires_at,
    )
    return GeneratedLinkCode(link_code=plaintext, expires_at=expires_at)


def link_telegram_account(
    *,
    one_time_code: str,
    telegram_chat_id: str | int,
    settings: Settings,
) -> str:
    if not is_valid_link_code_format(one_time_code):
        raise TelegramLinkRejectedError("Invalid or expired link code.")
    normalized_code = normalize_link_code(one_time_code)
    chat_id = _normalize_chat_id(telegram_chat_id)
    now = datetime.now(tz=UTC)
    row = fetch_active_link_code_by_hash(
        **_store_kwargs(settings),
        code_hash=hash_link_code(normalized_code),
    )
    if row is None:
        raise TelegramLinkRejectedError("Invalid or expired link code.")
    if _parse_expires_at(row.get("expires_at")) <= now:
        raise TelegramLinkRejectedError("Invalid or expired link code.")
    admin_id = str(row["admin_id"])
    encrypted = encrypt_telegram_chat_id(chat_id, environ=_crypto_environ(settings))
    update_admin_telegram_chat_id(
        **_store_kwargs(settings),
        admin_id=admin_id,
        telegram_chat_id_encrypted=encrypted,
    )
    mark_link_code_used(
        **_store_kwargs(settings),
        link_code_id=str(row["id"]),
        used_at=now,
    )
    return admin_id


def resolve_admin_id_from_telegram_chat_id(
    *,
    telegram_chat_id: str | int,
    settings: Settings,
) -> str:
    target = _normalize_chat_id(telegram_chat_id)
    for row in fetch_linked_admin_rows(**_store_kwargs(settings)):
        try:
            decrypted = decrypt_telegram_chat_id(
                row["telegram_chat_id_encrypted"],
                environ=_crypto_environ(settings),
            )
        except Exception:
            continue
        if decrypted == target:
            return row["id"]
    raise TelegramAdminNotLinkedError(
        "No linked admin account matches this Telegram chat."
    )
