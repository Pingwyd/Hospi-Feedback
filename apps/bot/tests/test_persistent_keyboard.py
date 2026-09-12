"""Tests for persistent Menu/Cancel reply keyboard intercept and lifecycle."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bot.constants import (
    MENU_DISCARD_CONFIRM,
    PERSISTENT_CANCEL_LABEL,
    PERSISTENT_KEYBOARD_ATTACHED_KEY,
    PERSISTENT_MENU_LABEL,
    REPORT_DRAFT_KEY,
    REPORT_MEMBER,
    REPORT_SEVERITY,
    STATUS_TICKET_KEY,
)
from bot.handlers.menu import handle_menu_callback
from bot.handlers.persistent_keyboard import try_handle_persistent_keyboard
from bot.handlers.report import receive_description, receive_member_text
from bot.handlers.status import receive_status_code, status_chat_message
from bot.keyboards import persistent_reply_keyboard, remove_persistent_keyboard
from bot.persistent_keyboard_lifecycle import attach_persistent_keyboard
from bot.sessions import store_access_session
from telegram.ext import ConversationHandler


def _store_valid_session(user_data: dict) -> None:
    expires = (datetime.now(tz=UTC) + timedelta(hours=1)).isoformat()
    store_access_session(user_data, token="session-token", expires_at=expires)


def test_persistent_reply_keyboard_has_menu_and_cancel() -> None:
    keyboard = persistent_reply_keyboard()
    labels = [button.text for row in keyboard.keyboard for button in row]
    assert labels == [PERSISTENT_MENU_LABEL, PERSISTENT_CANCEL_LABEL]


def test_remove_persistent_keyboard_returns_markup() -> None:
    assert remove_persistent_keyboard().remove_keyboard is True


@pytest.mark.asyncio
async def test_attach_persistent_keyboard_sets_attached_flag() -> None:
    message = AsyncMock()
    user_data: dict = {}

    await attach_persistent_keyboard(message, user_data)

    assert user_data[PERSISTENT_KEYBOARD_ATTACHED_KEY] is True
    message.reply_text.assert_awaited_once()
    assert (
        message.reply_text.await_args.kwargs["reply_markup"]
        == persistent_reply_keyboard()
    )


@pytest.mark.asyncio
async def test_try_handle_persistent_keyboard_routes_menu() -> None:
    update = MagicMock()
    update.message = AsyncMock()
    update.message.text = PERSISTENT_MENU_LABEL
    context = MagicMock()

    with patch(
        "bot.handlers.persistent_keyboard.menu_command",
        new=AsyncMock(return_value=ConversationHandler.END),
    ) as menu_command:
        result = await try_handle_persistent_keyboard(update, context)

    assert result == ConversationHandler.END
    menu_command.assert_awaited_once_with(update, context)


@pytest.mark.asyncio
async def test_try_handle_persistent_keyboard_routes_cancel() -> None:
    update = MagicMock()
    update.message = AsyncMock()
    update.message.text = PERSISTENT_CANCEL_LABEL
    context = MagicMock()

    with patch(
        "bot.handlers.persistent_keyboard.cancel_command",
        new=AsyncMock(return_value=ConversationHandler.END),
    ) as cancel_command:
        result = await try_handle_persistent_keyboard(update, context)

    assert result == ConversationHandler.END
    cancel_command.assert_awaited_once_with(update, context)


@pytest.mark.asyncio
async def test_try_handle_persistent_keyboard_ignores_substrings() -> None:
    update = MagicMock()
    update.message = AsyncMock()
    update.message.text = "please cancel this appointment"
    context = MagicMock()

    result = await try_handle_persistent_keyboard(update, context)

    assert result is False


@pytest.mark.asyncio
async def test_receive_description_intercepts_exact_menu_label() -> None:
    update = MagicMock()
    update.message = AsyncMock()
    update.message.text = PERSISTENT_MENU_LABEL
    context = MagicMock()
    context.user_data = {}
    _store_valid_session(context.user_data)

    with patch(
        "bot.handlers.report.try_handle_persistent_keyboard",
        new=AsyncMock(return_value=ConversationHandler.END),
    ) as intercept:
        state = await receive_description(update, context)

    assert state == ConversationHandler.END
    intercept.assert_awaited_once_with(update, context)


@pytest.mark.asyncio
async def test_receive_description_stores_normal_text() -> None:
    update = MagicMock()
    update.message = AsyncMock()
    update.message.text = "Leaky sink in block B."
    update.message.reply_text = AsyncMock()
    context = MagicMock()
    context.user_data = {}
    _store_valid_session(context.user_data)

    with patch(
        "bot.handlers.report.ensure_session_or_prompt",
        new=AsyncMock(return_value=True),
    ):
        state = await receive_description(update, context)

    assert state == REPORT_MEMBER
    assert (
        context.user_data[REPORT_DRAFT_KEY]["description"] == "Leaky sink in block B."
    )


@pytest.mark.asyncio
async def test_receive_description_intercepts_exact_cancel_label() -> None:
    update = MagicMock()
    update.message = AsyncMock()
    update.message.text = PERSISTENT_CANCEL_LABEL
    context = MagicMock()
    context.user_data = {}

    with patch(
        "bot.handlers.report.try_handle_persistent_keyboard",
        new=AsyncMock(return_value=ConversationHandler.END),
    ) as intercept:
        state = await receive_description(update, context)

    assert state == ConversationHandler.END
    intercept.assert_awaited_once_with(update, context)


@pytest.mark.asyncio
async def test_receive_member_text_passes_through_menu_substring() -> None:
    update = MagicMock()
    update.message = AsyncMock()
    update.message.text = "menu options were unclear"
    context = MagicMock()
    context.user_data = {
        REPORT_DRAFT_KEY: {"report_type": "complaint", "description": "x"}
    }

    with (
        patch(
            "bot.handlers.report.try_handle_persistent_keyboard",
            new=AsyncMock(return_value=False),
        ),
        patch(
            "bot.handlers.report._ask_severity",
            new=AsyncMock(return_value=REPORT_SEVERITY),
        ) as ask_severity,
    ):
        state = await receive_member_text(update, context)

    assert state == REPORT_SEVERITY
    assert (
        context.user_data[REPORT_DRAFT_KEY]["reported_member_name"]
        == "menu options were unclear"
    )
    ask_severity.assert_awaited_once()


@pytest.mark.asyncio
async def test_receive_status_code_intercepts_menu_before_ticket_validation() -> None:
    update = MagicMock()
    update.message = AsyncMock()
    update.message.text = PERSISTENT_MENU_LABEL
    context = MagicMock()

    with patch(
        "bot.handlers.status.try_handle_persistent_keyboard",
        new=AsyncMock(return_value=ConversationHandler.END),
    ) as intercept:
        state = await receive_status_code(update, context)

    assert state == ConversationHandler.END
    intercept.assert_awaited_once_with(update, context)


@pytest.mark.asyncio
async def test_status_chat_message_intercepts_exact_cancel_label() -> None:
    update = MagicMock()
    update.message = AsyncMock()
    update.message.text = PERSISTENT_CANCEL_LABEL
    context = MagicMock()
    context.user_data = {STATUS_TICKET_KEY: "ABCD2345"}

    with patch(
        "bot.handlers.status.try_handle_persistent_keyboard",
        new=AsyncMock(return_value=ConversationHandler.END),
    ) as intercept:
        await status_chat_message(update, context)

    intercept.assert_awaited_once_with(update, context)


@pytest.mark.asyncio
async def test_status_chat_message_skips_intercept_without_active_ticket() -> None:
    update = MagicMock()
    update.message = AsyncMock()
    update.message.text = PERSISTENT_CANCEL_LABEL
    context = MagicMock()
    context.user_data = {}

    with patch(
        "bot.handlers.status.try_handle_persistent_keyboard",
        new=AsyncMock(),
    ) as intercept:
        await status_chat_message(update, context)

    intercept.assert_not_called()


@pytest.mark.asyncio
async def test_cancel_from_report_flow_does_not_double_fire_in_status_handler() -> None:
    update = MagicMock()
    update.message = AsyncMock()
    update.message.text = PERSISTENT_CANCEL_LABEL
    update.message.reply_text = AsyncMock()
    context = MagicMock()
    context.user_data = {REPORT_DRAFT_KEY: {"report_type": "complaint"}}

    cancel_calls = 0

    async def _counting_cancel(*args, **kwargs):
        nonlocal cancel_calls
        cancel_calls += 1
        return ConversationHandler.END

    with patch(
        "bot.handlers.report.try_handle_persistent_keyboard",
        new=AsyncMock(side_effect=_counting_cancel),
    ):
        state = await receive_description(update, context)

    assert state == ConversationHandler.END
    assert cancel_calls == 1

    with patch(
        "bot.handlers.status.try_handle_persistent_keyboard",
        new=AsyncMock(),
    ) as status_intercept:
        await status_chat_message(update, context)

    status_intercept.assert_not_called()


@pytest.mark.asyncio
async def test_menu_then_report_type_switch_triggers_discard_confirm() -> None:
    menu_update = MagicMock()
    menu_update.message = AsyncMock()
    menu_update.message.text = PERSISTENT_MENU_LABEL
    menu_update.callback_query = None
    context = MagicMock()
    context.user_data = {
        REPORT_DRAFT_KEY: {
            "report_type": "complaint",
            "description": "Draft still in progress.",
        }
    }
    _store_valid_session(context.user_data)

    with (
        patch(
            "bot.handlers.start.ensure_persistent_keyboard",
            new=AsyncMock(),
        ),
        patch(
            "bot.handlers.start.show_main_menu",
            new=AsyncMock(),
        ) as show_main_menu,
    ):
        from bot.handlers.start import menu_command

        state = await menu_command(menu_update, context)

    assert state == ConversationHandler.END
    show_main_menu.assert_awaited_once()
    assert REPORT_DRAFT_KEY in context.user_data

    switch_update = MagicMock()
    switch_update.callback_query = AsyncMock()
    switch_update.callback_query.data = "menu:suggestion"
    switch_update.callback_query.message = AsyncMock()
    switch_update.message = None

    switch_state = await handle_menu_callback(switch_update, context)

    assert switch_state == MENU_DISCARD_CONFIRM
