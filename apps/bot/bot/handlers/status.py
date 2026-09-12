"""/status command, ticket lookup, and status chat."""

from __future__ import annotations

import io
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
from bot.handlers.persistent_keyboard import try_handle_persistent_keyboard
from bot.handlers.status_attachments import (
    PHOTO_PLACEHOLDER,
    iter_status_attachment_previews,
)
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
            if item.get("attachment") and content == PHOTO_PLACEHOLDER:
                lines.append(f"- ({sender}) [photo attached below]")
            else:
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


def _extension_for_content_type(content_type: str) -> str:
    lowered = content_type.lower()
    if "png" in lowered:
        return "png"
    if "webp" in lowered:
        return "webp"
    return "jpg"


async def _send_attachment_photo(
    chat_id: int,
    context: ContextTypes.DEFAULT_TYPE,
    *,
    api: HospiApiClient,
    token: str,
    caption: str,
    preview_url: str,
) -> None:
    try:
        data, content_type = await api.fetch_attachment_bytes(
            token=token,
            preview_url=preview_url,
        )
    except ApiClientError:
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"{caption}\nPhoto could not be loaded.",
        )
        return
    extension = _extension_for_content_type(content_type)
    buffer = io.BytesIO(data)
    buffer.name = f"attachment.{extension}"
    await context.bot.send_photo(
        chat_id=chat_id,
        photo=buffer,
        caption=caption[:1024],
    )


async def _send_status_attachment_previews(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    *,
    api: HospiApiClient,
    token: str,
    payload: dict,
) -> None:
    chat = update.effective_chat
    if chat is None:
        return
    for caption, preview_url in iter_status_attachment_previews(payload):
        await _send_attachment_photo(
            chat.id,
            context,
            api=api,
            token=token,
            caption=caption,
            preview_url=preview_url,
        )


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
    await _send_status_attachment_previews(
        update,
        context,
        api=api,
        token=token,
        payload=payload,
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
    handled = await try_handle_persistent_keyboard(update, context)
    if handled is not False:
        return handled
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
    handled = await try_handle_persistent_keyboard(update, context)
    if handled is not False:
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


async def status_chat_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or not update.message.photo:
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
    photo = update.message.photo[-1]
    try:
        await _enforce_rate_limit(update, context)
        telegram_file = await context.bot.get_file(photo.file_id)
        photo_bytes = bytes(await telegram_file.download_as_bytearray())
        result = await api.upload_attachment(
            token=token,
            ticket_code=ticket_code,
            filename="telegram-followup.jpg",
            content_type="image/jpeg",
            data=photo_bytes,
            link_to_thread=True,
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
                "Could not upload your photo. Try again in a moment."
            )
        return
    preview_url = result.get("preview_url")
    if isinstance(preview_url, str) and preview_url.strip():
        await _send_attachment_photo(
            update.effective_chat.id,
            context,
            api=api,
            token=token,
            caption="Your follow-up photo",
            preview_url=preview_url,
        )
    else:
        await update.message.reply_text("Photo sent.")
