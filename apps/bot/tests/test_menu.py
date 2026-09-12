"""Tests for main menu routing, discard confirm, and session gate."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bot.constants import (
    ACCESS_CODE,
    HELP_TEXT,
    MENU_DISCARD_CONFIRM,
    REPORT_DESCRIPTION,
    REPORT_DRAFT_KEY,
    REPORT_FLOW_STATE_KEY,
    REPORT_MEMBER,
    SESSION_EXPIRED_ACCESS_CODE_MSG,
    STATUS_AWAIT_CODE,
)
from bot.handlers.menu import (
    draft_is_in_progress,
    handle_menu_callback,
    handle_menu_go_callback,
    handle_menu_keep_callback,
)
from bot.handlers.start import menu_command
from bot.keyboards import main_menu_keyboard
from bot.report_labels import report_type_label
from bot.sessions import store_access_session
from telegram.ext import ConversationHandler


def _store_valid_session(user_data: dict) -> None:
    expires = (datetime.now(tz=UTC) + timedelta(hours=1)).isoformat()
    store_access_session(user_data, token="session-token", expires_at=expires)


def _callback_update(data: str) -> MagicMock:
    update = MagicMock()
    update.callback_query = AsyncMock()
    update.callback_query.data = data
    update.callback_query.message = AsyncMock()
    update.message = None
    return update


def _message_update(text: str = "/menu") -> MagicMock:
    update = MagicMock()
    update.message = AsyncMock()
    update.message.text = text
    update.callback_query = None
    return update


def test_main_menu_keyboard_matches_spec_labels() -> None:
    keyboard = main_menu_keyboard()
    labels = [row[0].text for row in keyboard.inline_keyboard]
    assert labels == [
        "Report Concern",
        "Suggest Something",
        "Shoutout",
        "Check Ticket Status",
        "Help",
    ]
    assert keyboard.inline_keyboard[2][0].callback_data == "menu:recognition"


def test_report_type_label_maps_recognition_to_shoutout() -> None:
    assert report_type_label("recognition") == "Shoutout"
    assert report_type_label("complaint") == "Report Concern"


def test_draft_is_in_progress_requires_progress_fields() -> None:
    user_data: dict = {REPORT_DRAFT_KEY: {"report_type": "complaint"}}
    assert draft_is_in_progress(user_data) is False
    user_data[REPORT_DRAFT_KEY]["description"] = "Leaky sink in block B."
    assert draft_is_in_progress(user_data) is True


@pytest.mark.asyncio
async def test_handle_menu_callback_starts_report_flow_for_each_type() -> None:
    for action in ("complaint", "suggestion", "recognition"):
        update = _callback_update(f"menu:{action}")
        context = MagicMock()
        context.user_data = {}
        _store_valid_session(context.user_data)

        state = await handle_menu_callback(update, context)

        assert state == REPORT_DESCRIPTION
        assert context.user_data[REPORT_DRAFT_KEY] == {"report_type": action}


@pytest.mark.asyncio
async def test_handle_menu_callback_routes_help_without_conversation() -> None:
    update = _callback_update("menu:help")
    context = MagicMock()
    context.user_data = {}
    _store_valid_session(context.user_data)

    state = await handle_menu_callback(update, context)

    assert state == ConversationHandler.END
    update.callback_query.message.reply_text.assert_awaited_once_with(HELP_TEXT)


@pytest.mark.asyncio
async def test_handle_menu_callback_routes_status_without_discard_confirm() -> None:
    update = _callback_update("menu:status")
    context = MagicMock()
    context.user_data = {
        REPORT_DRAFT_KEY: {
            "report_type": "complaint",
            "description": "Draft still in progress.",
        }
    }
    _store_valid_session(context.user_data)

    state = await handle_menu_callback(update, context)

    assert state == STATUS_AWAIT_CODE
    assert REPORT_DRAFT_KEY in context.user_data
    update.callback_query.message.reply_text.assert_awaited_once()


@pytest.mark.asyncio
async def test_handle_menu_callback_prompts_discard_for_report_type_switch() -> None:
    update = _callback_update("menu:suggestion")
    context = MagicMock()
    context.user_data = {
        REPORT_DRAFT_KEY: {
            "report_type": "complaint",
            "description": "Draft still in progress.",
        },
        REPORT_FLOW_STATE_KEY: REPORT_MEMBER,
    }
    _store_valid_session(context.user_data)

    state = await handle_menu_callback(update, context)

    assert state == MENU_DISCARD_CONFIRM
    reply_kwargs = update.callback_query.message.reply_text.await_args.kwargs
    assert "Discard and continue" in str(reply_kwargs["reply_markup"].inline_keyboard)


@pytest.mark.asyncio
async def test_handle_menu_go_clears_draft_and_starts_new_report() -> None:
    update = _callback_update("menu_go:suggestion")
    context = MagicMock()
    context.user_data = {
        REPORT_DRAFT_KEY: {
            "report_type": "complaint",
            "description": "Old draft.",
        },
        REPORT_FLOW_STATE_KEY: REPORT_MEMBER,
    }
    _store_valid_session(context.user_data)

    state = await handle_menu_go_callback(update, context)

    assert state == REPORT_DESCRIPTION
    assert context.user_data[REPORT_DRAFT_KEY] == {"report_type": "suggestion"}


@pytest.mark.asyncio
async def test_handle_menu_keep_resumes_saved_flow_state() -> None:
    update = _callback_update("menu_keep")
    context = MagicMock()
    context.user_data = {
        REPORT_DRAFT_KEY: {
            "report_type": "complaint",
            "description": "Draft still in progress.",
        },
        REPORT_FLOW_STATE_KEY: REPORT_MEMBER,
    }

    state = await handle_menu_keep_callback(update, context)

    assert state == REPORT_MEMBER
    update.callback_query.message.reply_text.assert_awaited_once()


@pytest.mark.asyncio
async def test_handle_menu_callback_expired_session_returns_access_code() -> None:
    update = _callback_update("menu:help")
    context = MagicMock()
    context.user_data = {}

    state = await handle_menu_callback(update, context)

    assert state == ACCESS_CODE
    update.callback_query.message.reply_text.assert_awaited_once_with(
        SESSION_EXPIRED_ACCESS_CODE_MSG
    )


@pytest.mark.asyncio
async def test_menu_command_shows_menu_with_valid_session() -> None:
    update = _message_update()
    context = MagicMock()
    context.user_data = {}
    _store_valid_session(context.user_data)

    with patch(
        "bot.handlers.start.show_main_menu",
        new=AsyncMock(),
    ) as show_menu:
        state = await menu_command(update, context)

    assert state == ConversationHandler.END
    show_menu.assert_awaited_once_with(update, context)


@pytest.mark.asyncio
async def test_menu_command_expired_session_returns_access_code() -> None:
    update = _message_update()
    context = MagicMock()
    context.user_data = {}

    state = await menu_command(update, context)

    assert state == ACCESS_CODE
    update.message.reply_text.assert_awaited_once_with(SESSION_EXPIRED_ACCESS_CODE_MSG)
