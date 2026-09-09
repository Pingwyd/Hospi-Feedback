"""Send ticket-bearing messages with the spec delete button."""

from __future__ import annotations

from typing import Any

from telegram import Update
from telegram.ext import ContextTypes

from bot.delete_targets import register_delete_target
from bot.keyboards import delete_message_keyboard


async def send_with_delete_button(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    *,
    text: str,
    parse_mode: str | None = None,
) -> None:
    chat = update.effective_chat
    if chat is None:
        return
    message = await chat.send_message(text, parse_mode=parse_mode)
    await message.edit_reply_markup(
        reply_markup=delete_message_keyboard(message.message_id)
    )
    user_data: dict[str, Any] = context.user_data
    register_delete_target(
        user_data,
        chat_id=chat.id,
        message_id=message.message_id,
    )
