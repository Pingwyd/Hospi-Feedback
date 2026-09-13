"""Tests for active /status session live admin-reply relay."""

from __future__ import annotations

import inspect
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bot.constants import STATUS_TICKET_KEY
from bot.handlers.status import load_ticket
from bot.live_relay import (
    LIVE_RELAY_REGISTRY_KEY,
    LiveRelaySession,
    clear_status_ticket_session,
    poll_status_live_relays,
    register_live_relay,
)
from bot.sessions import store_access_session
from telegram.ext import Application


def _store_valid_session(user_data: dict) -> None:
    expires = (datetime.now(tz=UTC) + timedelta(hours=1)).isoformat()
    store_access_session(user_data, token="session-token", expires_at=expires)


def _ticket_payload(*, messages: list[dict] | None = None) -> dict:
    return {
        "status": "new",
        "report_type": "complaint",
        "description": "Test",
        "messages": messages or [],
        "report_attachments": [],
    }


def _build_poll_context(
    *,
    user_data: dict,
    chat_id: int = 42,
    registry: dict | None = None,
) -> tuple[MagicMock, Application]:
    application = Application.builder().token("test-token").build()
    application.bot_data["api_client"] = AsyncMock()
    if registry is not None:
        application.bot_data[LIVE_RELAY_REGISTRY_KEY] = registry

    context = MagicMock()
    context.application = application
    context.bot = AsyncMock()
    return context, application, user_data, chat_id


@pytest.mark.asyncio
async def test_poll_delivers_new_admin_message_for_active_session() -> None:
    chat_id = 42
    user_data = {STATUS_TICKET_KEY: "ABCD2345"}
    _store_valid_session(user_data)
    registry = {
        chat_id: LiveRelaySession(
            chat_id=chat_id,
            ticket_code="ABCD2345",
            known_message_ids={"msg-reporter"},
        )
    }
    context, application, user_data, chat_id = _build_poll_context(
        user_data=user_data,
        chat_id=chat_id,
        registry=registry,
    )
    application.bot_data["api_client"].get_ticket_status = AsyncMock(
        return_value=_ticket_payload(
            messages=[
                {"id": "msg-reporter", "sender_type": "reporter", "content": "Hi"},
                {
                    "id": "msg-admin",
                    "sender_type": "admin",
                    "content": "We are reviewing this.",
                },
            ]
        )
    )

    with patch(
        "bot.live_relay._user_data_for_chat",
        return_value=user_data,
    ):
        await poll_status_live_relays(context)

    context.bot.send_message.assert_awaited_once()
    sent_text = context.bot.send_message.await_args.kwargs["text"]
    assert sent_text.startswith("New reply:")
    assert "(admin) We are reviewing this." in sent_text
    assert "msg-admin" in registry[chat_id].known_message_ids


@pytest.mark.asyncio
async def test_poll_skips_delivery_when_session_unregistered() -> None:
    chat_id = 42
    user_data = {STATUS_TICKET_KEY: "ABCD2345"}
    _store_valid_session(user_data)
    context, application, user_data, chat_id = _build_poll_context(
        user_data=user_data,
        chat_id=chat_id,
    )
    application.bot_data["api_client"].get_ticket_status = AsyncMock(
        return_value=_ticket_payload(
            messages=[
                {
                    "id": "msg-admin",
                    "sender_type": "admin",
                    "content": "Late reply.",
                }
            ]
        )
    )

    with patch(
        "bot.live_relay._user_data_for_chat",
        return_value=user_data,
    ):
        await poll_status_live_relays(context)

    context.bot.send_message.assert_not_awaited()
    application.bot_data["api_client"].get_ticket_status.assert_not_awaited()


@pytest.mark.asyncio
async def test_poll_does_not_echo_reporter_messages() -> None:
    chat_id = 42
    user_data = {STATUS_TICKET_KEY: "ABCD2345"}
    _store_valid_session(user_data)
    registry = {
        chat_id: LiveRelaySession(
            chat_id=chat_id,
            ticket_code="ABCD2345",
            known_message_ids=set(),
        )
    }
    context, application, user_data, chat_id = _build_poll_context(
        user_data=user_data,
        chat_id=chat_id,
        registry=registry,
    )
    application.bot_data["api_client"].get_ticket_status = AsyncMock(
        return_value=_ticket_payload(
            messages=[
                {
                    "id": "msg-reporter",
                    "sender_type": "reporter",
                    "content": "Just sent this.",
                }
            ]
        )
    )

    with patch(
        "bot.live_relay._user_data_for_chat",
        return_value=user_data,
    ):
        await poll_status_live_relays(context)

    context.bot.send_message.assert_not_awaited()
    assert "msg-reporter" in registry[chat_id].known_message_ids


@pytest.mark.asyncio
async def test_poll_discards_results_if_unregistered_during_fetch() -> None:
    chat_id = 42
    user_data = {STATUS_TICKET_KEY: "ABCD2345"}
    _store_valid_session(user_data)
    registry = {
        chat_id: LiveRelaySession(
            chat_id=chat_id,
            ticket_code="ABCD2345",
            known_message_ids=set(),
        )
    }
    context, application, user_data, chat_id = _build_poll_context(
        user_data=user_data,
        chat_id=chat_id,
        registry=registry,
    )

    async def fetch_and_unregister(*_args, **_kwargs):
        registry.pop(chat_id, None)
        return _ticket_payload(
            messages=[
                {
                    "id": "msg-admin",
                    "sender_type": "admin",
                    "content": "Should not send.",
                }
            ]
        )

    application.bot_data["api_client"].get_ticket_status = AsyncMock(
        side_effect=fetch_and_unregister
    )

    with patch(
        "bot.live_relay._user_data_for_chat",
        return_value=user_data,
    ):
        await poll_status_live_relays(context)

    context.bot.send_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_clear_status_ticket_session_unregisters_live_relay() -> None:
    application = Application.builder().token("test-token").build()
    user_data = {STATUS_TICKET_KEY: "ABCD2345"}
    register_live_relay(
        application,
        chat_id=99,
        ticket_code="ABCD2345",
        known_message_ids=set(),
    )

    clear_status_ticket_session(user_data, application, 99)

    assert STATUS_TICKET_KEY not in user_data
    assert application.bot_data[LIVE_RELAY_REGISTRY_KEY] == {}


@pytest.mark.asyncio
async def test_load_ticket_registers_live_relay_with_existing_messages() -> None:
    chat_id = 55
    user_data: dict = {}
    _store_valid_session(user_data)
    update = MagicMock()
    update.effective_chat = MagicMock(id=chat_id)
    update.message = AsyncMock()
    update.callback_query = None

    context = MagicMock()
    context.user_data = user_data
    context.application = Application.builder().token("test-token").build()
    context.application.bot_data["settings"] = MagicMock(
        telegram_identifier_pepper="pepper"
    )
    api = AsyncMock()
    api.get_ticket_status = AsyncMock(
        return_value=_ticket_payload(
            messages=[
                {
                    "id": "msg-admin-old",
                    "sender_type": "admin",
                    "content": "Already here.",
                }
            ]
        )
    )
    api.check_rate_limit = AsyncMock()
    context.application.bot_data["api_client"] = api

    with (
        patch(
            "bot.handlers.status.ensure_session_or_prompt",
            new=AsyncMock(return_value=True),
        ),
        patch(
            "bot.handlers.status.send_with_delete_button",
            new=AsyncMock(),
        ),
        patch(
            "bot.handlers.status._send_status_attachment_previews",
            new=AsyncMock(),
        ),
        patch(
            "bot.handlers.status._enforce_rate_limit",
            new=AsyncMock(),
        ),
    ):
        loaded = await load_ticket(update, context, "ABCD2345")

    assert loaded is True
    registry = context.application.bot_data[LIVE_RELAY_REGISTRY_KEY]
    assert registry[chat_id].known_message_ids == {"msg-admin-old"}


@pytest.mark.asyncio
async def test_poll_fetches_once_per_active_session_per_tick() -> None:
    """Two concurrent sessions should produce two API calls per 30s tick, not N^2."""
    sessions: dict[int, LiveRelaySession] = {
        10: LiveRelaySession(
            chat_id=10,
            ticket_code="ABCD2345",
            known_message_ids=set(),
        ),
        20: LiveRelaySession(
            chat_id=20,
            ticket_code="WXYZ6789",
            known_message_ids=set(),
        ),
    }
    user_data_by_chat: dict[int, dict] = {}
    for chat_id, code in ((10, "ABCD2345"), (20, "WXYZ6789")):
        data = {STATUS_TICKET_KEY: code}
        _store_valid_session(data)
        user_data_by_chat[chat_id] = data

    context, application, _, _ = _build_poll_context(
        user_data=user_data_by_chat[10],
        chat_id=10,
        registry=sessions,
    )
    application.bot_data["api_client"].get_ticket_status = AsyncMock(
        return_value=_ticket_payload(messages=[])
    )

    def _lookup(_application, chat_id: int):
        return user_data_by_chat.get(chat_id)

    with patch("bot.live_relay._user_data_for_chat", side_effect=_lookup):
        await poll_status_live_relays(context)

    assert application.bot_data["api_client"].get_ticket_status.await_count == 2


def test_poll_call_site_documents_rate_limit_exemption() -> None:
    source = inspect.getsourcefile(poll_status_live_relays)
    assert source is not None
    text = open(source, encoding="utf-8").read()
    assert "exempt from reporter-initiated rate limiting" in text.lower()
