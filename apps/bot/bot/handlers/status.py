"""/status command, ticket lookup, and status chat."""

from __future__ import annotations

import io
import re

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from bot.api_client import ApiClientError, HospiApiClient
from bot.constants import (
    PERSISTENT_CANCEL_LABEL,
    PERSISTENT_MENU_LABEL,
    STATUS_ASYNC_NOTE,
    STATUS_AWAIT_CODE,
    STATUS_PENDING_PHOTOS_KEY,
    STATUS_PENDING_PHOTOS_PROMPT_MSG_ID,
    STATUS_PHOTOS_DISCARD_CALLBACK,
    STATUS_PHOTOS_SEND_CALLBACK,
    STATUS_TICKET_KEY,
    TICKET_CODE_ALPHABET,
    TICKET_CODE_LENGTH,
)
from bot.handlers.auth_gate import ensure_session_or_prompt
from bot.handlers.persistent_keyboard import try_handle_persistent_keyboard
from bot.handlers.status_attachments import (
    PHOTO_PLACEHOLDER,
    _attachment_dicts_for_message,
    iter_message_attachment_previews,
    iter_status_attachment_previews,
)
from bot.keyboards import status_pending_photos_keyboard
from bot.telegram_utils import safe_answer_callback_query
from bot.hashing import hash_telegram_identifier
from bot.live_relay import (
    clear_status_ticket_session,
    collect_message_ids,
    register_live_relay,
)
from bot.messages import send_with_delete_button
from bot.session_flags import clear_awaiting_status_code
from bot.sessions import access_token

TICKET_CODE_PATTERN = re.compile(rf"^[{TICKET_CODE_ALPHABET}]{{{TICKET_CODE_LENGTH}}}$")


def normalize_ticket_code(raw: str) -> str | None:
    candidate = raw.strip().upper()
    if TICKET_CODE_PATTERN.fullmatch(candidate):
        return candidate
    return None


def format_status_message_line(item: dict) -> str:
    sender = item.get("sender_type", "unknown")
    content = item.get("content", "")
    attachment_count = len(_attachment_dicts_for_message(item))
    if attachment_count > 0 and content == PHOTO_PLACEHOLDER:
        if attachment_count > 1:
            return f"- ({sender}) [{attachment_count} photos attached below]"
        return f"- ({sender}) [photo attached below]"
    return f"- ({sender}) {content}"


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
            lines.append(format_status_message_line(item))
    lines.append("")
    lines.append(STATUS_ASYNC_NOTE)
    lines.append(
        "Reply in this chat to send a message on this ticket. "
        "Admin replies arrive automatically while this session is open."
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


async def deliver_live_admin_messages(
    context: ContextTypes.DEFAULT_TYPE,
    *,
    chat_id: int,
    api: HospiApiClient,
    token: str,
    messages: list[dict],
) -> None:
    for message in messages:
        for caption, preview_url in iter_message_attachment_previews(message):
            await _send_attachment_photo(
                chat_id,
                context,
                api=api,
                token=token,
                caption=caption,
                preview_url=preview_url,
            )


def _pending_photo_file_ids(user_data: dict) -> list[str]:
    raw = user_data.get(STATUS_PENDING_PHOTOS_KEY)
    if not isinstance(raw, list):
        return []
    return [item for item in raw if isinstance(item, str) and item]


async def _update_pending_photos_prompt(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    *,
    photo_count: int,
) -> None:
    if update.effective_chat is None:
        return
    text = (
        f"{photo_count} photo(s) ready. Send them to the team or discard the selection."
        if photo_count > 0
        else "No photos selected."
    )
    keyboard = status_pending_photos_keyboard(photo_count=photo_count)
    prompt_id = context.user_data.get(STATUS_PENDING_PHOTOS_PROMPT_MSG_ID)
    if isinstance(prompt_id, int):
        try:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=prompt_id,
                text=text,
                reply_markup=keyboard,
            )
            return
        except Exception:
            context.user_data.pop(STATUS_PENDING_PHOTOS_PROMPT_MSG_ID, None)
    sent = await update.effective_chat.send_message(text, reply_markup=keyboard)
    context.user_data[STATUS_PENDING_PHOTOS_PROMPT_MSG_ID] = sent.message_id


async def _download_telegram_photo_bytes(
    context: ContextTypes.DEFAULT_TYPE,
    file_id: str,
) -> bytes:
    telegram_file = await context.bot.get_file(file_id)
    return bytes(await telegram_file.download_as_bytearray())


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
    chat = update.effective_chat
    if chat is not None:
        register_live_relay(
            context.application,
            chat_id=chat.id,
            ticket_code=ticket_code,
            known_message_ids=collect_message_ids(payload),
        )
    clear_awaiting_status_code(context.user_data)
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
    text = update.message.text.strip()
    if text in (PERSISTENT_MENU_LABEL, PERSISTENT_CANCEL_LABEL):
        # ConversationHandler (group 0) already routes Menu/Cancel labels.
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
            clear_status_ticket_session(
                context.user_data,
                context.application,
                update.effective_chat.id if update.effective_chat else None,
            )
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
    photo = update.message.photo[-1]
    pending = _pending_photo_file_ids(context.user_data)
    if photo.file_id not in pending:
        pending.append(photo.file_id)
    context.user_data[STATUS_PENDING_PHOTOS_KEY] = pending
    await _update_pending_photos_prompt(update, context, photo_count=len(pending))


async def status_pending_photos_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    query = update.callback_query
    if query is None or query.data is None:
        return
    ticket_code = context.user_data.get(STATUS_TICKET_KEY)
    if not isinstance(ticket_code, str):
        await safe_answer_callback_query(query)
        return
    if not await ensure_session_or_prompt(update, context):
        return
    api: HospiApiClient = context.application.bot_data["api_client"]
    token = access_token(context.user_data)
    if token is None:
        await safe_answer_callback_query(query)
        return

    if query.data == STATUS_PHOTOS_DISCARD_CALLBACK:
        await safe_answer_callback_query(query)
        context.user_data.pop(STATUS_PENDING_PHOTOS_KEY, None)
        context.user_data.pop(STATUS_PENDING_PHOTOS_PROMPT_MSG_ID, None)
        if query.message is not None:
            await query.message.edit_text("Photos discarded.")
        return

    if query.data != STATUS_PHOTOS_SEND_CALLBACK:
        await safe_answer_callback_query(query)
        return

    pending = _pending_photo_file_ids(context.user_data)
    if not pending:
        await safe_answer_callback_query(query, text="No photos selected.")
        return

    await safe_answer_callback_query(query, text="Uploading photos...")
    try:
        await _enforce_rate_limit(update, context)
        file_payloads: list[tuple[str, bytes, str]] = []
        for index, file_id in enumerate(pending, start=1):
            photo_bytes = await _download_telegram_photo_bytes(context, file_id)
            file_payloads.append(
                (f"telegram-followup-{index}.jpg", photo_bytes, "image/jpeg"),
            )
        result = await api.upload_attachments_batch(
            token=token,
            ticket_code=ticket_code,
            files=file_payloads,
        )
    except ApiClientError as exc:
        if exc.status_code == 429:
            await query.message.reply_text(
                "You have sent too many requests. Try again later."
            )
        elif exc.status_code == 409:
            await query.message.reply_text("This ticket is closed.")
            clear_status_ticket_session(
                context.user_data,
                context.application,
                update.effective_chat.id if update.effective_chat else None,
            )
        else:
            await query.message.reply_text(
                "Could not upload your photos. Try again in a moment."
            )
        return

    context.user_data.pop(STATUS_PENDING_PHOTOS_KEY, None)
    context.user_data.pop(STATUS_PENDING_PHOTOS_PROMPT_MSG_ID, None)
    attachments = result.get("attachments") or []
    if isinstance(attachments, list) and attachments:
        count = len(attachments)
        if query.message is not None:
            await query.message.edit_text(
                f"{count} photo(s) sent to the team."
                if count > 1
                else "Photo sent to the team."
            )
        for index, attachment in enumerate(attachments, start=1):
            if not isinstance(attachment, dict):
                continue
            preview_url = attachment.get("preview_url")
            if not isinstance(preview_url, str) or not preview_url.strip():
                continue
            caption = "Your follow-up photo"
            if count > 1:
                caption = f"Your follow-up photo {index}"
            await _send_attachment_photo(
                update.effective_chat.id,
                context,
                api=api,
                token=token,
                caption=caption,
                preview_url=preview_url,
            )
    elif query.message is not None:
        await query.message.edit_text("Photo sent.")
