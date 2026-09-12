"""Main menu rendering and menu callback routing."""

from __future__ import annotations

from typing import Any

from telegram import Message, Update
from telegram.ext import ContextTypes, ConversationHandler

from bot.constants import (
    ACCESS_CODE,
    DISCARD_REPORT_CONFIRM_MSG,
    HELP_TEXT,
    MENU_CALLBACK_PREFIX,
    MENU_DISCARD_CONFIRM,
    MENU_GO_CALLBACK_PREFIX,
    REPORT_CONFIRM,
    REPORT_DESCRIPTION,
    REPORT_DRAFT_KEY,
    REPORT_FLOW_STATE_KEY,
    REPORT_MEMBER,
    REPORT_PHOTO,
    REPORT_SEVERITY,
    SESSION_EXPIRED_ACCESS_CODE_MSG,
    STATUS_AWAIT_CODE,
    STATUS_TICKET_KEY,
)
from bot.keyboards import (
    discard_confirm_keyboard,
    main_menu_keyboard,
    severity_keyboard,
    skip_keyboard,
)
from bot.sessions import clear_access_session, has_valid_access_session

_REPORT_TYPE_ACTIONS = frozenset({"complaint", "suggestion", "recognition"})
_DRAFT_PROGRESS_KEYS = frozenset(
    {"description", "reported_member_name", "severity", "photo_file_id"}
)


def draft_is_in_progress(user_data: dict[str, Any]) -> bool:
    draft = user_data.get(REPORT_DRAFT_KEY)
    if not isinstance(draft, dict) or not draft:
        return False
    return bool(_DRAFT_PROGRESS_KEYS & draft.keys())


def _clear_stale_session_data(user_data: dict[str, Any]) -> None:
    clear_access_session(user_data)
    user_data.pop(REPORT_DRAFT_KEY, None)
    user_data.pop(REPORT_FLOW_STATE_KEY, None)
    user_data.pop(STATUS_TICKET_KEY, None)


async def prompt_expired_session_access_code(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    if query is not None:
        await query.answer()
        target = query.message
    else:
        target = update.message
    _clear_stale_session_data(context.user_data)
    if target is not None:
        await target.reply_text(SESSION_EXPIRED_ACCESS_CODE_MSG)
    return ACCESS_CODE


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


async def _send_resume_prompt(
    message: Message, context: ContextTypes.DEFAULT_TYPE, resume_state: int
) -> None:
    draft = context.user_data.get(REPORT_DRAFT_KEY)
    if resume_state == REPORT_DESCRIPTION:
        await message.reply_text(
            "Describe what happened or what you want to share. "
            "Be as specific as you can."
        )
        return
    if resume_state == REPORT_MEMBER:
        await message.reply_text(
            "Optional: name a member involved, or tap Skip.",
            reply_markup=skip_keyboard(),
        )
        return
    if resume_state == REPORT_SEVERITY:
        await message.reply_text(
            "Optional: choose a severity, or tap Skip.",
            reply_markup=severity_keyboard(),
        )
        return
    if resume_state == REPORT_PHOTO:
        await message.reply_text(
            "Optional: send one photo, or tap Skip.",
            reply_markup=skip_keyboard(),
        )
        return
    if resume_state == REPORT_CONFIRM and isinstance(draft, dict):
        from bot.handlers.report import _show_confirm

        await _show_confirm(message, context)


async def _route_menu_action(
    message: Message | None,
    context: ContextTypes.DEFAULT_TYPE,
    action: str,
) -> int:
    if message is None:
        return ConversationHandler.END
    if action == "help":
        await message.reply_text(HELP_TEXT)
        return ConversationHandler.END
    if action == "status":
        context.user_data.pop(STATUS_TICKET_KEY, None)
        await message.reply_text(
            "Send your 8-character ticket code, or use /status <code>."
        )
        return STATUS_AWAIT_CODE
    if action in _REPORT_TYPE_ACTIONS:
        context.user_data.pop(STATUS_TICKET_KEY, None)
        context.user_data[REPORT_DRAFT_KEY] = {"report_type": action}
        context.user_data[REPORT_FLOW_STATE_KEY] = REPORT_DESCRIPTION
        await message.reply_text(
            "Describe what happened or what you want to share. "
            "Be as specific as you can."
        )
        return REPORT_DESCRIPTION
    return ConversationHandler.END


async def handle_menu_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int | None:
    query = update.callback_query
    if query is None or query.data is None or query.message is None:
        return ConversationHandler.END
    if not has_valid_access_session(context.user_data):
        return await prompt_expired_session_access_code(update, context)
    await query.answer()
    action = query.data.removeprefix(MENU_CALLBACK_PREFIX)
    if action in _REPORT_TYPE_ACTIONS and draft_is_in_progress(context.user_data):
        context.user_data[REPORT_FLOW_STATE_KEY] = context.user_data.get(
            REPORT_FLOW_STATE_KEY, REPORT_DESCRIPTION
        )
        await query.message.reply_text(
            DISCARD_REPORT_CONFIRM_MSG,
            reply_markup=discard_confirm_keyboard(action),
        )
        return MENU_DISCARD_CONFIRM
    return await _route_menu_action(query.message, context, action)


async def handle_menu_go_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    if query is None or query.data is None or query.message is None:
        return ConversationHandler.END
    if not has_valid_access_session(context.user_data):
        return await prompt_expired_session_access_code(update, context)
    await query.answer()
    action = query.data.removeprefix(MENU_GO_CALLBACK_PREFIX)
    context.user_data.pop(REPORT_DRAFT_KEY, None)
    context.user_data.pop(REPORT_FLOW_STATE_KEY, None)
    return await _route_menu_action(query.message, context, action)


async def handle_menu_keep_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    if query is None or query.message is None:
        return ConversationHandler.END
    await query.answer()
    resume_state = context.user_data.get(REPORT_FLOW_STATE_KEY, REPORT_DESCRIPTION)
    if not isinstance(resume_state, int):
        resume_state = REPORT_DESCRIPTION
    await _send_resume_prompt(query.message, context, resume_state)
    return resume_state
