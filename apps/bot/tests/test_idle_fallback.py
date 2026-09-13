"""Tests for idle-state unrecognized text nudge."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bot.config import BotSettings
from bot.constants import (
    AWAITING_ACCESS_CODE_KEY,
    IDLE_UNRECOGNIZED_TEXT_NUDGE,
    LAPSED_SESSION_NUDGE,
    PERSISTENT_CANCEL_LABEL,
    PERSISTENT_KEYBOARD_ATTACHED_KEY,
    PERSISTENT_MENU_LABEL,
    REPORT_DESCRIPTION,
    REPORT_DRAFT_KEY,
    REPORT_FLOW_STATE_KEY,
    REPORT_MEMBER,
    STATUS_TICKET_KEY,
    UNAUTHENTICATED_FIRST_TOUCH_NUDGE,
)
from bot.handlers.idle_fallback import idle_unrecognized_text
from bot.handlers.report import receive_description
from bot.handlers.status import receive_status_code, status_chat_message
from bot.main import build_application
from bot.session_flags import (
    is_first_touch_for_nudge,
    is_idle_for_nudge,
    is_lapsed_session_for_nudge,
    set_awaiting_status_code,
)
from bot.sessions import store_access_session
from telegram.ext import MessageHandler


def _store_valid_session(user_data: dict) -> None:
    expires = (datetime.now(tz=UTC) + timedelta(hours=1)).isoformat()
    store_access_session(user_data, token="session-token", expires_at=expires)


def _idle_user_data() -> dict:
    user_data: dict = {}
    _store_valid_session(user_data)
    return user_data


def test_is_idle_for_nudge_requires_valid_access_session() -> None:
    assert is_idle_for_nudge({}) is False


def test_is_idle_for_nudge_true_for_idle_session() -> None:
    assert is_idle_for_nudge(_idle_user_data()) is True


def test_is_idle_for_nudge_false_with_active_ticket() -> None:
    user_data = _idle_user_data()
    user_data[STATUS_TICKET_KEY] = "ABCD2345"
    assert is_idle_for_nudge(user_data) is False


def test_is_idle_for_nudge_false_during_report_flow() -> None:
    user_data = _idle_user_data()
    user_data[REPORT_FLOW_STATE_KEY] = REPORT_DESCRIPTION
    assert is_idle_for_nudge(user_data) is False


def test_is_idle_for_nudge_false_while_awaiting_status_code() -> None:
    user_data = _idle_user_data()
    set_awaiting_status_code(user_data)
    assert is_idle_for_nudge(user_data) is False


def test_is_first_touch_for_nudge_true_for_empty_user_data() -> None:
    assert is_first_touch_for_nudge({}) is True


def test_is_first_touch_for_nudge_false_while_awaiting_access_code() -> None:
    user_data: dict = {AWAITING_ACCESS_CODE_KEY: True}
    assert is_first_touch_for_nudge(user_data) is False


def test_is_lapsed_session_for_nudge_true_with_keyboard_flag() -> None:
    user_data = {PERSISTENT_KEYBOARD_ATTACHED_KEY: True}
    assert is_lapsed_session_for_nudge(user_data) is True
    assert is_first_touch_for_nudge(user_data) is False


@pytest.mark.asyncio
async def test_first_touch_nudge_fires_before_start() -> None:
    update = MagicMock()
    update.message = AsyncMock()
    update.message.text = "hello?"
    context = MagicMock()
    context.user_data = {}

    await idle_unrecognized_text(update, context)

    update.message.reply_text.assert_awaited_once_with(UNAUTHENTICATED_FIRST_TOUCH_NUDGE)


@pytest.mark.asyncio
async def test_lapsed_session_nudge_not_first_touch_copy() -> None:
    update = MagicMock()
    update.message = AsyncMock()
    update.message.text = "hello?"
    context = MagicMock()
    context.user_data = {PERSISTENT_KEYBOARD_ATTACHED_KEY: True}

    await idle_unrecognized_text(update, context)

    update.message.reply_text.assert_awaited_once_with(LAPSED_SESSION_NUDGE)


@pytest.mark.asyncio
async def test_access_code_entry_does_not_trigger_group_two_nudge() -> None:
    update = MagicMock()
    update.message = AsyncMock()
    update.message.text = "not-the-code"
    context = MagicMock()
    context.user_data = {AWAITING_ACCESS_CODE_KEY: True}

    await idle_unrecognized_text(update, context)

    update.message.reply_text.assert_not_awaited()


@pytest.mark.asyncio
async def test_idle_nudge_fires_for_unrecognized_text() -> None:
    update = MagicMock()
    update.message = AsyncMock()
    update.message.text = "roarrr"
    context = MagicMock()
    context.user_data = _idle_user_data()

    await idle_unrecognized_text(update, context)

    update.message.reply_text.assert_awaited_once_with(IDLE_UNRECOGNIZED_TEXT_NUDGE)


@pytest.mark.asyncio
async def test_idle_nudge_fires_on_every_unrecognized_message() -> None:
    update = MagicMock()
    update.message = AsyncMock()
    update.message.text = "first"
    context = MagicMock()
    context.user_data = _idle_user_data()

    await idle_unrecognized_text(update, context)
    update.message.text = "second"
    await idle_unrecognized_text(update, context)

    assert update.message.reply_text.await_count == 2


@pytest.mark.asyncio
async def test_idle_nudge_skips_menu_and_cancel_labels() -> None:
    context = MagicMock()
    context.user_data = _idle_user_data()

    for label in (PERSISTENT_MENU_LABEL, PERSISTENT_CANCEL_LABEL):
        update = MagicMock()
        update.message = AsyncMock()
        update.message.text = label
        await idle_unrecognized_text(update, context)
        update.message.reply_text.assert_not_awaited()


@pytest.mark.asyncio
async def test_active_status_session_posts_to_ticket_without_nudge() -> None:
    update = MagicMock()
    update.message = AsyncMock()
    update.message.text = "follow up note"
    update.effective_chat = MagicMock(id=42)
    context = MagicMock()
    context.user_data = _idle_user_data()
    context.user_data[STATUS_TICKET_KEY] = "ABCD2345"
    context.application.bot_data = {
        "api_client": AsyncMock(),
        "settings": MagicMock(telegram_identifier_pepper="pepper"),
    }
    context.application.bot_data["api_client"].post_ticket_message = AsyncMock()

    with (
        patch(
            "bot.handlers.status.ensure_session_or_prompt",
            new=AsyncMock(return_value=True),
        ),
        patch(
            "bot.handlers.status._enforce_rate_limit",
            new=AsyncMock(),
        ),
        patch(
            "bot.handlers.status.try_handle_persistent_keyboard",
            new=AsyncMock(return_value=False),
        ),
    ):
        await status_chat_message(update, context)
        await idle_unrecognized_text(update, context)

    context.application.bot_data["api_client"].post_ticket_message.assert_awaited_once()
    assert update.message.reply_text.await_count == 1
    assert update.message.reply_text.await_args.args[0] == "Message sent."


@pytest.mark.asyncio
async def test_report_description_captures_text_without_idle_nudge() -> None:
    update = MagicMock()
    update.message = AsyncMock()
    update.message.text = "Something happened in the ward."
    update.callback_query = None
    context = MagicMock()
    context.user_data = _idle_user_data()
    context.user_data[REPORT_DRAFT_KEY] = {"report_type": "complaint"}
    context.user_data[REPORT_FLOW_STATE_KEY] = REPORT_DESCRIPTION

    with patch(
        "bot.handlers.report.ensure_session_or_prompt",
        new=AsyncMock(return_value=True),
    ):
        state = await receive_description(update, context)
        await idle_unrecognized_text(update, context)

    assert state == REPORT_MEMBER
    assert context.user_data[REPORT_DRAFT_KEY]["description"] == (
        "Something happened in the ward."
    )
    reply_calls = [
        call.args[0] for call in update.message.reply_text.await_args_list
    ]
    assert IDLE_UNRECOGNIZED_TEXT_NUDGE not in reply_calls


@pytest.mark.asyncio
async def test_awaiting_status_code_uses_invalid_code_handling_not_idle_nudge() -> None:
    update = MagicMock()
    update.message = AsyncMock()
    update.message.text = "not-a-code"
    update.callback_query = None
    context = MagicMock()
    context.user_data = _idle_user_data()
    set_awaiting_status_code(context.user_data)

    with patch(
        "bot.handlers.status.try_handle_persistent_keyboard",
        new=AsyncMock(return_value=False),
    ):
        state = await receive_status_code(update, context)
        await idle_unrecognized_text(update, context)

    assert state == 7  # STATUS_AWAIT_CODE
    update.message.reply_text.assert_awaited_once_with(
        "Enter a valid 8-character ticket code, or /cancel to stop."
    )


def test_build_application_registers_idle_handler_in_group_two() -> None:
    settings = BotSettings(
        telegram_bot_token="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
        telegram_identifier_pepper="pepper",
        api_base_url="http://test",
        bot_service_secret="secret",
    )
    application = build_application(settings)
    group_two = application.handlers[2]
    idle_handlers = [
        handler
        for handler in group_two
        if isinstance(handler, MessageHandler)
        and handler.callback is idle_unrecognized_text
    ]
    assert len(idle_handlers) == 1
