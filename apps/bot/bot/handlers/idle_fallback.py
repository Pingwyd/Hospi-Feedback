"""Low-priority nudge when unrecognized text is not handled elsewhere."""

from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from bot.constants import (
    IDLE_UNRECOGNIZED_TEXT_NUDGE,
    LAPSED_SESSION_NUDGE,
    PERSISTENT_CANCEL_LABEL,
    PERSISTENT_MENU_LABEL,
    UNAUTHENTICATED_FIRST_TOUCH_NUDGE,
)
from bot.session_flags import (
    is_first_touch_for_nudge,
    is_idle_for_nudge,
    is_lapsed_session_for_nudge,
)


async def idle_unrecognized_text(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    if update.message is None or update.message.text is None:
        return
    text = update.message.text.strip()
    if text in (PERSISTENT_MENU_LABEL, PERSISTENT_CANCEL_LABEL):
        return

    user_data = context.user_data
    if is_idle_for_nudge(user_data):
        await update.message.reply_text(IDLE_UNRECOGNIZED_TEXT_NUDGE)
        return
    if is_first_touch_for_nudge(user_data):
        await update.message.reply_text(UNAUTHENTICATED_FIRST_TOUCH_NUDGE)
        return
    if is_lapsed_session_for_nudge(user_data):
        await update.message.reply_text(LAPSED_SESSION_NUDGE)
