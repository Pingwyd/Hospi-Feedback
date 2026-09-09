"""/status command, ticket lookup, and status chat."""

from __future__ import annotations

import re

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from bot.api_client import ApiClientError, HospiApiClient
from bot.constants import (
    STATUS_ASYNC_NOTE,
    STATUS_AWAIT_CODE,
    STATUS_TICKET_KEY,
    TICKET_CODE_ALPHABET,
    TICKET_CODE_LENGTH,
)
from bot.handlers.auth_gate import ensure_session_or_prompt
from bot.hashing import hash_telegram_identifier
from bot.messages import send_with_delete_button
from bot.sessions import access_token

TICKET_CODE_PATTERN = re.compile(rf"^[{TICKET_CODE_ALPHABET}]{{{TICKET_CODE_LENGTH}}}$")


def normalize_ticket_code(raw: str) -> str | None:
    candidate = raw.strip().upper()
    if TICKET_CODE_PATTERN.fullmatch(candidate):
        return candidate
    return None


def format_ticket_status(payload: dict) -> str:
    lines = [
        f"Status: {payload.get('status', 'unknown')}",
        f"Type: {payload.get('report_type', 'unknown')}",
        f"Description: {payload.get('description', '')}",
    ]
    member = payload.get("reported_member_name")
    if member:
        lines.append(f"Member named: {member}")
    severity = payload.get("severity")
    if severity:
        lines.append(f"Severity: {severity}")
    messages = payload.get("messages") or []
    if messages:
        lines.append("")
        lines.append("Messages:")
        for item in messages:
            sender = item.get("sender_type", "unknown")
            content = item.get("content", "")
            lines.append(f"- ({sender}) {content}")
    lines.append("")
    lines.append(STATUS_ASYNC_NOTE)
    lines.append(
        "Reply in this chat to send a message on this ticket "
        "while your session is active."
    )
    return "\n".join(lines)


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


async def load_ticket(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    ticket_code: str,
) -> bool:
    if not await ensure_session_or_prompt(update, context):
        return False
    api: HospiApiClient = context.application.bot_data["api_client"]
    token = access_token(context.user_data)
    if token is None:
        return False
    try:
        await _enforce_rate_limit(update, context)
        payload = await api.get_ticket_status(token=token, ticket_code=ticket_code)
    except ApiClientError as exc:
        target = update.message
        if target is None and update.callback_query is not None:
            target = update.callback_query.message
        if target is not None:
            if exc.status_code == 429:
                await target.reply_text(
                    "You have sent too many requests. Try again later."
                )
            elif exc.status_code == 404:
                await target.reply_text(
                    "No ticket found with that code. Check the code and try again."
                )
            else:
                await target.reply_text(
                    "Could not load that ticket. Try again in a moment."
                )
        return False
    context.user_data[STATUS_TICKET_KEY] = ticket_code
    body = format_ticket_status(payload)
    await send_with_delete_button(
        update,
        context,
        text=f"Ticket `{ticket_code}`\n\n{body}",
        parse_mode="Markdown",
    )
    return True


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return
    if not context.args:
        await update.message.reply_text("Usage: /status <ticket-code>")
        return
    ticket_code = normalize_ticket_code(context.args[0])
    if ticket_code is None:
        await update.message.reply_text(
            "Enter a valid 8-character ticket code from your submission."
        )
        return
    await load_ticket(update, context, ticket_code)


async def receive_status_code(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    if update.message is None or update.message.text is None:
        return STATUS_AWAIT_CODE
    ticket_code = normalize_ticket_code(update.message.text)
    if ticket_code is None:
        await update.message.reply_text(
            "Enter a valid 8-character ticket code, or /cancel to stop."
        )
        return STATUS_AWAIT_CODE
    await load_ticket(update, context, ticket_code)
    return ConversationHandler.END


async def status_chat_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    if update.message is None or update.message.text is None:
        return
    ticket_code = context.user_data.get(STATUS_TICKET_KEY)
    if not isinstance(ticket_code, str):
        return
    if not await ensure_session_or_prompt(update, context):
        return
    api: HospiApiClient = context.application.bot_data["api_client"]
    token = access_token(context.user_data)
    if token is None:
        return
    try:
        await _enforce_rate_limit(update, context)
        await api.post_ticket_message(
            token=token,
            ticket_code=ticket_code,
            content=update.message.text.strip(),
        )
    except ApiClientError as exc:
        if exc.status_code == 429:
            await update.message.reply_text(
                "You have sent too many requests. Try again later."
            )
        elif exc.status_code == 409:
            await update.message.reply_text("This ticket is closed.")
            context.user_data.pop(STATUS_TICKET_KEY, None)
        else:
            await update.message.reply_text(
                "Could not send your message. Try again in a moment."
            )
        return
    await update.message.reply_text("Message sent.")
