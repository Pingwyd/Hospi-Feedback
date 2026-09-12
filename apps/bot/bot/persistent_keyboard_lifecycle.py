"""Attach the persistent Menu/Cancel reply keyboard after session verification."""

from __future__ import annotations

from typing import Any

from telegram import Message

from bot.constants import PERSISTENT_KEYBOARD_ATTACHED_KEY
from bot.keyboards import persistent_reply_keyboard


async def attach_persistent_keyboard(
    message: Message, user_data: dict[str, Any]
) -> None:
    await message.reply_text(
        "Access granted.",
        reply_markup=persistent_reply_keyboard(),
    )
    user_data[PERSISTENT_KEYBOARD_ATTACHED_KEY] = True


async def ensure_persistent_keyboard(
    message: Message, user_data: dict[str, Any]
) -> None:
    if user_data.get(PERSISTENT_KEYBOARD_ATTACHED_KEY):
        return
    await message.reply_text(
        "Use Menu or Cancel below at any time.",
        reply_markup=persistent_reply_keyboard(),
    )
    user_data[PERSISTENT_KEYBOARD_ATTACHED_KEY] = True
