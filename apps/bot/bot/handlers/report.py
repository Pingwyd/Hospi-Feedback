"""Guided reporter submission flow."""

from __future__ import annotations

from typing import Any

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from bot.api_client import ApiClientError, HospiApiClient
from bot.constants import (
    CONFIRM_CANCEL,
    CONFIRM_SUBMIT,
    PRIVACY_NOTICE,
    REPORT_CALLBACK_PREFIX,
    REPORT_CONFIRM,
    REPORT_DESCRIPTION,
    REPORT_DRAFT_KEY,
    REPORT_FLOW_STATE_KEY,
    REPORT_MEMBER,
    REPORT_PHOTO,
    REPORT_SEVERITY,
    SKIP_CALLBACK,
)
from bot.handlers.auth_gate import ensure_session_or_prompt
from bot.handlers.menu import show_main_menu
from bot.handlers.persistent_keyboard import try_handle_persistent_keyboard
from bot.hashing import hash_telegram_identifier
from bot.keyboards import confirm_keyboard, severity_keyboard, skip_keyboard
from bot.messages import send_with_delete_button
from bot.report_labels import report_type_label
from bot.sessions import access_token

SUMMARY_TEMPLATE = (
    "Review your report:\n"
    "Type: {report_type}\n"
    "Description: {description}\n"
    "Member named: {member}\n"
    "Severity: {severity}\n"
    "Photo: {photo}\n\n"
    "{privacy}\n\n"
    "Submit when ready."
)


def _draft(user_data: dict[str, Any]) -> dict[str, Any]:
    draft = user_data.setdefault(REPORT_DRAFT_KEY, {})
    if not isinstance(draft, dict):
        draft = {}
        user_data[REPORT_DRAFT_KEY] = draft
    return draft


async def _enforce_rate_limit(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    settings = context.application.bot_data["settings"]
    api: HospiApiClient = context.application.bot_data["api_client"]
    token = access_token(context.user_data)
    if token is None:
        raise ApiClientError(401, "unauthorized", "Session expired.")
    chat_id = update.effective_chat.id if update.effective_chat else None
    if chat_id is None:
        raise ApiClientError(400, "bad_request", "Missing chat.")
    identifier_hash = hash_telegram_identifier(
        chat_id,
        pepper=settings.telegram_identifier_pepper,
    )
    await api.check_rate_limit(token=token, identifier_hash=identifier_hash)


async def receive_description(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    if update.message is None or update.message.text is None:
        return REPORT_DESCRIPTION
    handled = await try_handle_persistent_keyboard(update, context)
    if handled is not False:
        return handled
    if not await ensure_session_or_prompt(update, context):
        return ConversationHandler.END
    description = update.message.text.strip()
    if not description:
        await update.message.reply_text("Please enter a description.")
        return REPORT_DESCRIPTION
    _draft(context.user_data)["description"] = description
    context.user_data[REPORT_FLOW_STATE_KEY] = REPORT_MEMBER
    await update.message.reply_text(
        "Optional: name a member involved, or tap Skip.",
        reply_markup=skip_keyboard(),
    )
    return REPORT_MEMBER


async def receive_member_text(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    if update.message is None or update.message.text is None:
        return REPORT_MEMBER
    handled = await try_handle_persistent_keyboard(update, context)
    if handled is not False:
        return handled
    _draft(context.user_data)["reported_member_name"] = update.message.text.strip()
    context.user_data[REPORT_FLOW_STATE_KEY] = REPORT_SEVERITY
    return await _ask_severity(update, context)


async def skip_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query is not None:
        await query.answer()
        message = query.message
    else:
        message = update.message
    if message is None:
        return REPORT_MEMBER
    context.user_data[REPORT_FLOW_STATE_KEY] = REPORT_SEVERITY
    await message.reply_text(
        "Optional: choose a severity, or tap Skip.",
        reply_markup=severity_keyboard(),
    )
    return REPORT_SEVERITY


async def _ask_severity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    message = update.message
    if message is None and update.callback_query is not None:
        message = update.callback_query.message
    if message is None:
        return REPORT_SEVERITY
    context.user_data[REPORT_FLOW_STATE_KEY] = REPORT_SEVERITY
    await message.reply_text(
        "Optional: choose a severity, or tap Skip.",
        reply_markup=severity_keyboard(),
    )
    return REPORT_SEVERITY


async def receive_severity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query is None or query.data is None:
        return REPORT_SEVERITY
    await query.answer()
    if query.data == SKIP_CALLBACK:
        context.user_data[REPORT_FLOW_STATE_KEY] = REPORT_PHOTO
        return await _ask_photo(query.message, context)
    severity = query.data.removeprefix(REPORT_CALLBACK_PREFIX)
    if severity not in {"low", "medium", "high"}:
        return REPORT_SEVERITY
    _draft(context.user_data)["severity"] = severity
    context.user_data[REPORT_FLOW_STATE_KEY] = REPORT_PHOTO
    return await _ask_photo(query.message, context)


async def _ask_photo(message, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data[REPORT_FLOW_STATE_KEY] = REPORT_PHOTO
    await message.reply_text(
        "Optional: send one photo, or tap Skip.",
        reply_markup=skip_keyboard(),
    )
    return REPORT_PHOTO


async def receive_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None or not update.message.photo:
        return REPORT_PHOTO
    photo = update.message.photo[-1]
    _draft(context.user_data)["photo_file_id"] = photo.file_id
    return await _show_confirm(update.message, context)


async def skip_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query is None:
        return REPORT_PHOTO
    await query.answer()
    if query.message is None:
        return REPORT_PHOTO
    return await _show_confirm(query.message, context)


async def _show_confirm(message, context: ContextTypes.DEFAULT_TYPE) -> int:
    draft = _draft(context.user_data)
    report_type = str(draft.get("report_type", "unknown"))
    summary = SUMMARY_TEMPLATE.format(
        report_type=report_type_label(report_type),
        description=draft.get("description", ""),
        member=draft.get("reported_member_name") or "None",
        severity=draft.get("severity") or "None",
        photo="Yes" if draft.get("photo_file_id") else "No",
        privacy=PRIVACY_NOTICE,
    )
    context.user_data[REPORT_FLOW_STATE_KEY] = REPORT_CONFIRM
    await message.reply_text(summary, reply_markup=confirm_keyboard())
    return REPORT_CONFIRM


async def confirm_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query is None or query.message is None:
        return REPORT_CONFIRM
    await query.answer()
    if query.data == CONFIRM_CANCEL:
        context.user_data.pop(REPORT_DRAFT_KEY, None)
        context.user_data.pop(REPORT_FLOW_STATE_KEY, None)
        await query.message.reply_text("Report cancelled.")
        await show_main_menu(update, context)
        return ConversationHandler.END
    if query.data != CONFIRM_SUBMIT:
        return REPORT_CONFIRM
    if not await ensure_session_or_prompt(update, context):
        return ConversationHandler.END
    draft = _draft(context.user_data)
    api: HospiApiClient = context.application.bot_data["api_client"]
    token = access_token(context.user_data)
    if token is None:
        return ConversationHandler.END
    try:
        await _enforce_rate_limit(update, context)
        result = await api.create_report(
            token=token,
            report_type=draft["report_type"],
            description=draft["description"],
            reported_member_name=draft.get("reported_member_name"),
            severity=draft.get("severity"),
        )
        ticket_code = str(result["ticket_code"])
        photo_file_id = draft.get("photo_file_id")
        if isinstance(photo_file_id, str):
            telegram_file = await context.bot.get_file(photo_file_id)
            photo_bytes = bytes(await telegram_file.download_as_bytearray())
            await api.upload_attachment(
                token=token,
                ticket_code=ticket_code,
                filename="telegram-photo.jpg",
                content_type="image/jpeg",
                data=photo_bytes,
            )
    except ApiClientError as exc:
        if exc.status_code == 429:
            await query.message.reply_text(
                "You have sent too many requests. Try again later."
            )
        else:
            await query.message.reply_text(
                "Could not submit your report. Try again in a moment."
            )
        return ConversationHandler.END
    context.user_data.pop(REPORT_DRAFT_KEY, None)
    context.user_data.pop(REPORT_FLOW_STATE_KEY, None)
    await query.message.reply_text("Report submitted.")
    await send_with_delete_button(
        update,
        context,
        text=(
            f"Your ticket code is `{ticket_code}`.\n\n"
            "Save it somewhere safe. Use /status with this code to follow up."
        ),
        parse_mode="Markdown",
    )
    await show_main_menu(update, context)
    return ConversationHandler.END
