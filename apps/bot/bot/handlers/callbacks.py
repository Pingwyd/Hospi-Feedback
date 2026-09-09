"""Inline callback handlers."""

from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from bot.constants import DELETE_CALLBACK_PREFIX
from bot.delete_targets import owns_delete_target


async def delete_message_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    query = update.callback_query
    if query is None or query.data is None or query.message is None:
        return
    if not query.data.startswith(DELETE_CALLBACK_PREFIX):
        return
    suffix = query.data.removeprefix(DELETE_CALLBACK_PREFIX)
    if not suffix.isdigit():
        await query.answer("This button is no longer valid.")
        return
    message_id = int(suffix)
    chat_id = query.message.chat_id
    if not owns_delete_target(
        context.user_data,
        chat_id=chat_id,
        message_id=message_id,
    ):
        await query.answer("You cannot delete this message.")
        return
    await query.answer()
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception:
        await query.message.reply_text("Could not delete that message.")
