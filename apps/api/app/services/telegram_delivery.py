"""Resolve HOH Telegram chat id and deliver purge PDFs."""

from __future__ import annotations

from app.core.crypto import ENV_KEY_NAME, decrypt_telegram_chat_id
from app.core.settings import Settings
from app.integrations.telegram_admin_store import fetch_linked_admin_rows
from app.integrations.telegram_notify import send_telegram_document


def _store_kwargs(settings: Settings) -> dict[str, str]:
    return {
        "supabase_url": settings.supabase_url,
        "service_role_key": settings.supabase_service_role_key,
    }


def _crypto_environ(settings: Settings) -> dict[str, str]:
    return {ENV_KEY_NAME: settings.telegram_chat_id_encryption_key}


def resolve_hoh_telegram_chat_id(*, settings: Settings) -> str | None:
    """Return decrypted Telegram chat_id for the active HOH, if linked."""
    for row in fetch_linked_admin_rows(**_store_kwargs(settings)):
        if str(row.get("role") or "") != "hoh":
            continue
        encrypted = row.get("telegram_chat_id_encrypted")
        if not encrypted:
            continue
        try:
            return decrypt_telegram_chat_id(
                str(encrypted),
                environ=_crypto_environ(settings),
            )
        except Exception:
            continue
    return None


def deliver_purge_summary_pdf(
    *,
    settings: Settings,
    pdf_bytes: bytes,
    archived_count: int,
) -> bool:
    """Send purge summary PDF to linked HOH via Telegram. Returns True on success."""
    chat_id = resolve_hoh_telegram_chat_id(settings=settings)
    if not chat_id or not settings.telegram_bot_token.strip():
        return False
    send_telegram_document(
        bot_token=settings.telegram_bot_token,
        chat_id=chat_id,
        filename="purge-summary.pdf",
        content=pdf_bytes,
        caption=f"Scheduled purge complete. {archived_count} report(s) archived.",
    )
    return True
