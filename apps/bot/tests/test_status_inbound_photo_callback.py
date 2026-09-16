"""Tests for inbound photo quality and resend callbacks."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from bot.constants import (
    STATUS_PHOTO_AWAITING_SHOW_QUALITY_KEY,
    STATUS_PHOTO_INBOUND_QUEUE_KEY,
    STATUS_PHOTO_JPEG_QUALITY_KEY,
    STATUS_PHOTO_QUALITY_CALLBACK_PREFIX,
    STATUS_PHOTO_VIEW_MODE_KEY,
    STATUS_PHOTO_VIEW_SHOW,
    STATUS_TICKET_KEY,
)
from bot.handlers.status import status_inbound_photo_callback
from bot.inbound_photo_delivery import set_last_inbound_photo_batch
from bot.sessions import store_access_session
from datetime import UTC, datetime, timedelta
from telegram.ext import Application


def _store_valid_session(user_data: dict) -> None:
    expires = (datetime.now(tz=UTC) + timedelta(hours=1)).isoformat()
    store_access_session(user_data, token="session-token", expires_at=expires)


def _quality_callback_update(
    *,
    user_data: dict,
    quality: str = "90",
    chat_id: int = 99,
) -> tuple[MagicMock, MagicMock]:
    application = Application.builder().token("test-token").build()
    application.bot_data["api_client"] = AsyncMock()

    query = MagicMock()
    query.answer = AsyncMock()
    query.data = f"{STATUS_PHOTO_QUALITY_CALLBACK_PREFIX}{quality}"
    query.message = MagicMock()
    query.message.chat_id = chat_id
    query.message.edit_text = AsyncMock()

    update = MagicMock()
    update.callback_query = query

    context = MagicMock()
    context.application = application
    context.user_data = user_data
    context.bot = AsyncMock()

    return update, context


@pytest.mark.asyncio
async def test_quality_change_on_ticket_with_sent_photos_prompts_resend() -> None:
    user_data = {
        STATUS_TICKET_KEY: "ABCD2345",
        STATUS_PHOTO_VIEW_MODE_KEY: STATUS_PHOTO_VIEW_SHOW,
        STATUS_PHOTO_JPEG_QUALITY_KEY: 70,
    }
    _store_valid_session(user_data)
    set_last_inbound_photo_batch(
        user_data,
        [{"caption": "Photo", "preview_url": "/api/x/1"}],
    )
    update, context = _quality_callback_update(user_data=user_data)

    await status_inbound_photo_callback(update, context)

    update.callback_query.message.edit_text.assert_awaited()
    edit_args = update.callback_query.message.edit_text.await_args
    body = edit_args.args[0] if edit_args.args else edit_args.kwargs["text"]
    assert "Send or resend photo attachments" in body
    assert edit_args.kwargs.get("reply_markup") is not None
    assert user_data[STATUS_PHOTO_JPEG_QUALITY_KEY] == 90


@pytest.mark.asyncio
async def test_quality_change_off_ticket_does_not_prompt_resend() -> None:
    user_data = {STATUS_PHOTO_JPEG_QUALITY_KEY: 70}
    _store_valid_session(user_data)
    set_last_inbound_photo_batch(
        user_data,
        [{"caption": "Photo", "preview_url": "/api/x/1"}],
    )
    update, context = _quality_callback_update(user_data=user_data)

    await status_inbound_photo_callback(update, context)

    edit_args = update.callback_query.message.edit_text.await_args
    body = edit_args.args[0] if edit_args.args else edit_args.kwargs["text"]
    assert "reply_markup" not in edit_args.kwargs
    assert "/status" in body


@pytest.mark.asyncio
async def test_initial_show_quality_still_sends_without_resend_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_data = {
        STATUS_TICKET_KEY: "ABCD2345",
        STATUS_PHOTO_INBOUND_QUEUE_KEY: [
            {"caption": "Queued", "preview_url": "/api/x/q"},
        ],
        STATUS_PHOTO_AWAITING_SHOW_QUALITY_KEY: True,
    }
    _store_valid_session(user_data)
    update, context = _quality_callback_update(user_data=user_data, quality="70")

    flush = AsyncMock()
    monkeypatch.setattr("bot.handlers.status._flush_inbound_photo_queue", flush)

    await status_inbound_photo_callback(update, context)

    flush.assert_awaited_once()
    edit_args = update.callback_query.message.edit_text.await_args
    assert "reply_markup" not in edit_args.kwargs


@pytest.mark.asyncio
async def test_quality_via_command_with_pending_queue_prompts_resend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Matches /quality while show/skip is still unanswered: confirm, do not auto-send."""
    user_data = {
        STATUS_TICKET_KEY: "ABCD2345",
        STATUS_PHOTO_INBOUND_QUEUE_KEY: [
            {"caption": "Queued", "preview_url": "/api/x/q"},
        ],
    }
    _store_valid_session(user_data)
    update, context = _quality_callback_update(user_data=user_data, quality="90")

    flush = AsyncMock()
    monkeypatch.setattr("bot.handlers.status._flush_inbound_photo_queue", flush)

    await status_inbound_photo_callback(update, context)

    flush.assert_not_awaited()
    edit_args = update.callback_query.message.edit_text.await_args
    body = edit_args.args[0] if edit_args.args else edit_args.kwargs["text"]
    assert "Send or resend photo attachments" in body
    assert edit_args.kwargs.get("reply_markup") is not None
