"""Shared intercept for persistent reply-keyboard Menu and Cancel labels."""

from __future__ import annotations

from typing import Literal

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from bot.constants import PERSISTENT_CANCEL_LABEL, PERSISTENT_MENU_LABEL
from bot.handlers.start import cancel_command, menu_command

HandledState = int | None
InterceptResult = HandledState | Literal[False]


async def try_handle_persistent_keyboard(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> InterceptResult:
    """Route reserved reply-keyboard labels through existing command handlers."""
    if update.message is None or update.message.text is None:
        return False
    text = update.message.text.strip()
    if text == PERSISTENT_MENU_LABEL:
        state = await menu_command(update, context)
        if state is None:
            return ConversationHandler.END
        return state
    if text == PERSISTENT_CANCEL_LABEL:
        return await cancel_command(update, context)
    return False


async def handle_persistent_keyboard_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """ConversationHandler entry/fallback for Menu and Cancel reply labels."""
    handled = await try_handle_persistent_keyboard(update, context)
    if handled is False:
        return ConversationHandler.END
    return handled
