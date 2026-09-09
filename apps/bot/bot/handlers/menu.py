"""Main menu rendering and menu callback routing."""

from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from bot.constants import (
    HELP_TEXT,
    MENU_CALLBACK_PREFIX,
    REPORT_DESCRIPTION,
    REPORT_DRAFT_KEY,
    STATUS_AWAIT_CODE,
    STATUS_TICKET_KEY,
)
from bot.handlers.auth_gate import ensure_session_or_prompt
from bot.keyboards import main_menu_keyboard


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = "What would you like to do?"
    keyboard = main_menu_keyboard()
    if update.callback_query is not None:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, reply_markup=keyboard)
        return
    chat = update.effective_chat
    if chat is not None:
        await chat.send_message(text, reply_markup=keyboard)


async def handle_menu_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int | None:
    query = update.callback_query
    if query is None or query.data is None:
        return ConversationHandler.END
    if not await ensure_session_or_prompt(update, context):
        return ConversationHandler.END
    await query.answer()
    action = query.data.removeprefix(MENU_CALLBACK_PREFIX)
    if action == "help":
        await query.message.reply_text(HELP_TEXT)
        return ConversationHandler.END
    if action == "status":
        context.user_data.pop(STATUS_TICKET_KEY, None)
        await query.message.reply_text(
            "Send your 8-character ticket code, or use /status <code>."
        )
        return STATUS_AWAIT_CODE
    if action in {"complaint", "suggestion", "recognition"}:
        context.user_data.pop(STATUS_TICKET_KEY, None)
        context.user_data[REPORT_DRAFT_KEY] = {"report_type": action}
        await query.message.reply_text(
            "Describe what happened or what you want to share. "
            "Be as specific as you can."
        )
        return REPORT_DESCRIPTION
    return ConversationHandler.END
