"""Telegram API helpers."""

from __future__ import annotations

import logging

from telegram import CallbackQuery
from telegram.error import BadRequest

logger = logging.getLogger(__name__)


async def safe_answer_callback_query(
    query: CallbackQuery | None,
    *,
    text: str | None = None,
    show_alert: bool = False,
) -> None:
    """Answer a callback query without failing on expired query ids."""
    if query is None:
        return
    try:
        await query.answer(text=text, show_alert=show_alert)
    except BadRequest as exc:
        message = str(exc)
        if "query is too old" in message.lower() or "query id is invalid" in message.lower():
            logger.debug("Ignored stale callback query: %s", message)
            return
        raise
