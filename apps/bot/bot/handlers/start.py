"""/start, access code gate, and main menu."""

from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from bot.api_client import ApiClientError, HospiApiClient
from bot.constants import (
    ACCESS_CODE,
    HELP_TEXT,
    PERSISTENT_KEYBOARD_ATTACHED_KEY,
    REPORT_DRAFT_KEY,
    REPORT_FLOW_STATE_KEY,
    STATUS_TICKET_KEY,
)
from bot.handlers.menu import prompt_expired_session_access_code, show_main_menu
from bot.keyboards import remove_persistent_keyboard
from bot.persistent_keyboard_lifecycle import (
    attach_persistent_keyboard,
    ensure_persistent_keyboard,
)
from bot.sessions import (
    clear_access_session,
    has_valid_access_session,
    store_access_session,
)


async def start_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int | None:
    if update.message is None:
        return ConversationHandler.END
    context.user_data.pop(STATUS_TICKET_KEY, None)
    if has_valid_access_session(context.user_data):
        await ensure_persistent_keyboard(update.message, context.user_data)
        await show_main_menu(update, context)
        return ConversationHandler.END
    clear_access_session(context.user_data)
    context.user_data.pop(PERSISTENT_KEYBOARD_ATTACHED_KEY, None)
    await update.message.reply_text(
        "Welcome to Hospi Feedback.\n\n"
        "Enter the unit access code to continue. "
        "It is required once per session.",
        reply_markup=remove_persistent_keyboard(),
    )
    return ACCESS_CODE


async def receive_access_code(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    if update.message is None or update.message.text is None:
        return ACCESS_CODE
    api: HospiApiClient = context.application.bot_data["api_client"]
    try:
        payload = await api.verify_access_code(update.message.text.strip())
    except ApiClientError:
        await update.message.reply_text(
            "That access code is not valid. Try again or contact your unit lead."
        )
        return ACCESS_CODE
    token = payload.get("session_token")
    expires_at = payload.get("expires_at")
    if not isinstance(token, str) or not isinstance(expires_at, str):
        await update.message.reply_text(
            "Could not start a session. Try again in a moment."
        )
        return ACCESS_CODE
    store_access_session(
        context.user_data,
        token=token,
        expires_at=expires_at,
    )
    context.user_data.pop(STATUS_TICKET_KEY, None)
    await attach_persistent_keyboard(update.message, context.user_data)
    await show_main_menu(update, context)
    return ConversationHandler.END


async def menu_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int | None:
    if update.message is None:
        return ConversationHandler.END
    if has_valid_access_session(context.user_data):
        await ensure_persistent_keyboard(update.message, context.user_data)
        await show_main_menu(update, context)
        return ConversationHandler.END
    return await prompt_expired_session_access_code(update, context)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return
    await update.message.reply_text(HELP_TEXT)


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is not None:
        await update.message.reply_text("Cancelled.")
    context.user_data.pop(REPORT_DRAFT_KEY, None)
    context.user_data.pop(REPORT_FLOW_STATE_KEY, None)
    context.user_data.pop(STATUS_TICKET_KEY, None)
    if has_valid_access_session(context.user_data):
        await ensure_persistent_keyboard(update.message, context.user_data)
        await show_main_menu(update, context)
    return ConversationHandler.END
