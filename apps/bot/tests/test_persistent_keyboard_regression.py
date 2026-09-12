"""Application-level regression tests for persistent Menu + discard-confirm flow."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bot.config import BotSettings
from bot.constants import (
    MENU_DISCARD_CONFIRM,
    PERSISTENT_MENU_LABEL,
    REPORT_DRAFT_KEY,
)
from bot.handlers.menu import (
    _route_menu_action,
    draft_is_in_progress,
    handle_menu_callback,
)
from bot.handlers.persistent_keyboard import handle_persistent_keyboard_message
from bot.handlers.report import receive_member_text
from bot.handlers.start import menu_command
from bot.main import build_application
from bot.sessions import store_access_session
from telegram.ext import ConversationHandler, MessageHandler


def _store_valid_session(user_data: dict) -> None:
    expires = (datetime.now(tz=UTC) + timedelta(hours=1)).isoformat()
    store_access_session(user_data, token="session-token", expires_at=expires)


def test_build_application_has_no_second_persistent_keyboard_handler() -> None:
    """Hard Stop 1 guard: Menu/Cancel must not exist outside ConversationHandler."""
    settings = BotSettings(
        telegram_bot_token="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
        telegram_identifier_pepper="pepper",
        api_base_url="http://test",
        bot_service_secret="secret",
    )
    application = build_application(settings)
    group_zero_handlers = application.handlers[0]

    persistent_handlers = [
        handler
        for handler in group_zero_handlers
        if isinstance(handler, MessageHandler)
        and handler.callback is handle_persistent_keyboard_message
    ]
    assert persistent_handlers == []

    conversation_handlers = [
        handler
        for handler in group_zero_handlers
        if isinstance(handler, ConversationHandler)
    ]
    assert len(conversation_handlers) == 1


@pytest.mark.asyncio
async def test_persistent_menu_mid_report_preserves_draft_single_route() -> None:
    """Scenario 1 guard: persistent Menu must not clear report_draft."""
    update = MagicMock()
    update.message = AsyncMock()
    update.message.text = PERSISTENT_MENU_LABEL
    update.callback_query = None
    context = MagicMock()
    context.user_data = {
        REPORT_DRAFT_KEY: {
            "report_type": "complaint",
            "description": "yjtyjtjti",
        }
    }
    _store_valid_session(context.user_data)

    menu_calls = 0

    async def _counting_menu(*args, **kwargs):
        nonlocal menu_calls
        menu_calls += 1
        return ConversationHandler.END

    with patch(
        "bot.handlers.persistent_keyboard.menu_command",
        side_effect=_counting_menu,
    ):
        state = await receive_member_text(update, context)

    assert state == ConversationHandler.END
    assert menu_calls == 1
    assert context.user_data[REPORT_DRAFT_KEY]["description"] == "yjtyjtjti"
    assert draft_is_in_progress(context.user_data) is True


@pytest.mark.asyncio
async def test_end_state_menu_uses_conversation_fallback_not_second_handler() -> None:
    """Menu in END state must route once through ConversationHandler fallback."""
    update = MagicMock()
    update.message = AsyncMock()
    update.message.text = PERSISTENT_MENU_LABEL
    update.callback_query = None
    context = MagicMock()
    context.user_data = {}
    _store_valid_session(context.user_data)

    menu_calls = 0

    async def _counting_menu(*args, **kwargs):
        nonlocal menu_calls
        menu_calls += 1
        return ConversationHandler.END

    with patch(
        "bot.handlers.persistent_keyboard.menu_command",
        side_effect=_counting_menu,
    ):
        state = await handle_persistent_keyboard_message(update, context)

    assert state == ConversationHandler.END
    assert menu_calls == 1


@pytest.mark.asyncio
async def test_report_type_after_persistent_menu_triggers_discard_confirm() -> None:
    """Scenario 2 guard: inline report-type tap after persistent Menu must confirm."""
    menu_update = MagicMock()
    menu_update.message = AsyncMock()
    menu_update.message.text = PERSISTENT_MENU_LABEL
    menu_update.callback_query = None
    context = MagicMock()
    context.user_data = {
        REPORT_DRAFT_KEY: {
            "report_type": "complaint",
            "description": "yjtyjtjti",
        }
    }
    _store_valid_session(context.user_data)

    with (
        patch("bot.handlers.start.ensure_persistent_keyboard", new=AsyncMock()),
        patch("bot.handlers.start.show_main_menu", new=AsyncMock()),
    ):
        await menu_command(menu_update, context)

    assert draft_is_in_progress(context.user_data) is True

    switch_update = MagicMock()
    switch_update.callback_query = AsyncMock()
    switch_update.callback_query.data = "menu:suggestion"
    switch_update.callback_query.message = AsyncMock()
    switch_update.message = None

    route_calls = 0

    async def _counting_route(*args, **kwargs):
        nonlocal route_calls
        route_calls += 1
        return await _route_menu_action(*args, **kwargs)

    with patch(
        "bot.handlers.menu._route_menu_action",
        side_effect=_counting_route,
    ):
        state = await handle_menu_callback(switch_update, context)

    assert state == MENU_DISCARD_CONFIRM
    assert route_calls == 0
    switch_update.callback_query.message.reply_text.assert_awaited_once()


@pytest.mark.asyncio
async def test_full_reproduction_transcript_b_then_c() -> None:
    """Exact two-step reproduction from Hard Stop 2 transcripts B and C."""
    transcript: list[str] = []

    # B: mid-report persistent Menu
    menu_update = MagicMock()
    menu_update.message = AsyncMock()
    menu_update.message.text = PERSISTENT_MENU_LABEL
    menu_update.callback_query = None
    context = MagicMock()
    context.user_data = {
        REPORT_DRAFT_KEY: {
            "report_type": "complaint",
            "description": "yjtyjtjti",
        }
    }
    _store_valid_session(context.user_data)

    async def _show_menu(*args, **kwargs):
        transcript.append("Bot: What would you like to do? [inline menu]")

    with (
        patch("bot.handlers.start.ensure_persistent_keyboard", new=AsyncMock()),
        patch("bot.handlers.start.show_main_menu", side_effect=_show_menu),
    ):
        transcript.append('User: [ taps persistent "Menu" ]')
        await receive_member_text(menu_update, context)

    draft_after_menu = dict(context.user_data[REPORT_DRAFT_KEY])
    transcript.append(f"State: END | draft: {draft_after_menu}")

    # C: inline report-type switch
    switch_update = MagicMock()
    switch_update.callback_query = AsyncMock()
    switch_update.callback_query.data = "menu:suggestion"
    switch_update.callback_query.message = AsyncMock()
    switch_update.message = None

    async def _reply_discard(*args, **kwargs):
        transcript.append(
            "Bot: You have a report in progress. Discard it and continue?"
        )

    switch_update.callback_query.message.reply_text = AsyncMock(
        side_effect=_reply_discard
    )

    transcript.append('User: [ taps "Suggest Something" ]')
    state = await handle_menu_callback(switch_update, context)
    transcript.append(f"State: {state}")

    print("\n".join(transcript))

    assert draft_after_menu == {
        "report_type": "complaint",
        "description": "yjtyjtjti",
    }
    assert state == MENU_DISCARD_CONFIRM
    assert any("Discard it and continue" in line for line in transcript)
