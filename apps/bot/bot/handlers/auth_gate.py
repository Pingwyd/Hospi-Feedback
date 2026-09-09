"""Shared session gate for reporter handlers."""

from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from bot.sessions import has_valid_access_session


async def ensure_session_or_prompt(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> bool:
    if has_valid_access_session(context.user_data):
        return True
    if update.message is not None:
        await update.message.reply_text(
            "Your session expired. Send /start and enter the access code again."
        )
    elif update.callback_query is not None:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(
            "Your session expired. Send /start and enter the access code again."
        )
    return False
