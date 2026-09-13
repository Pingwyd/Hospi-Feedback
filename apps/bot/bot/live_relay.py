"""In-memory live relay for admin replies during active /status sessions."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from telegram.ext import Application, ContextTypes

from bot.constants import STATUS_TICKET_KEY
from bot.sessions import access_token

logger = logging.getLogger(__name__)

LIVE_RELAY_REGISTRY_KEY = "status_live_relay"
LIVE_RELAY_INTERVAL_SECONDS = 30


@dataclass
class LiveRelaySession:
    chat_id: int
    ticket_code: str
    known_message_ids: set[str] = field(default_factory=set)


def _registry(application: Application) -> dict[int, LiveRelaySession]:
    registry = application.bot_data.get(LIVE_RELAY_REGISTRY_KEY)
    if not isinstance(registry, dict):
        registry = {}
        application.bot_data[LIVE_RELAY_REGISTRY_KEY] = registry
    return registry


def register_live_relay(
    application: Application,
    *,
    chat_id: int,
    ticket_code: str,
    known_message_ids: set[str],
) -> None:
    _registry(application)[chat_id] = LiveRelaySession(
        chat_id=chat_id,
        ticket_code=ticket_code,
        known_message_ids=set(known_message_ids),
    )


def unregister_live_relay(application: Application, chat_id: int) -> None:
    _registry(application).pop(chat_id, None)


def clear_status_ticket_session(
    user_data: dict[str, Any],
    application: Application,
    chat_id: int | None,
) -> None:
    user_data.pop(STATUS_TICKET_KEY, None)
    if chat_id is not None:
        unregister_live_relay(application, chat_id)


def collect_message_ids(payload: dict[str, Any]) -> set[str]:
    ids: set[str] = set()
    for item in payload.get("messages") or []:
        message_id = item.get("id")
        if isinstance(message_id, str) and message_id:
            ids.add(message_id)
    return ids


def _user_data_for_chat(
    application: Application, chat_id: int
) -> dict[str, Any] | None:
    user_data = application.user_data.get(chat_id)
    if isinstance(user_data, dict):
        return user_data
    return None


def _session_still_active(
    application: Application,
    session: LiveRelaySession,
    user_data: dict[str, Any],
) -> bool:
    if session.chat_id not in _registry(application):
        return False
    ticket_code = user_data.get(STATUS_TICKET_KEY)
    if ticket_code != session.ticket_code:
        return False
    return access_token(user_data) is not None


async def poll_status_live_relays(context: ContextTypes.DEFAULT_TYPE) -> None:
    from bot.api_client import ApiClientError, HospiApiClient
    from bot.handlers.status import (
        deliver_live_admin_messages,
        format_status_message_line,
    )

    application = context.application
    registry = _registry(application)
    if not registry:
        return

    api: HospiApiClient = application.bot_data["api_client"]

    for chat_id in list(registry.keys()):
        session = registry.get(chat_id)
        if session is None:
            continue

        user_data = _user_data_for_chat(application, chat_id)
        if user_data is None or not _session_still_active(
            application, session, user_data
        ):
            unregister_live_relay(application, chat_id)
            continue

        token = access_token(user_data)
        if token is None:
            unregister_live_relay(application, chat_id)
            continue

        try:
            # This call is exempt from reporter-initiated rate limiting (background
            # poll for open /status sessions; see ticket-route rate-limit TODO).
            payload = await api.get_ticket_status(
                token=token,
                ticket_code=session.ticket_code,
            )
        except ApiClientError as exc:
            if exc.status_code == 409:
                clear_status_ticket_session(user_data, application, chat_id)
            elif exc.status_code in {401, 403, 404}:
                unregister_live_relay(application, chat_id)
            else:
                logger.warning(
                    "live_relay_poll_failed chat_id=%s ticket=%s status=%s",
                    chat_id,
                    session.ticket_code,
                    exc.status_code,
                )
            continue

        if chat_id not in registry:
            continue

        messages = payload.get("messages") or []
        new_admin_messages = [
            item
            for item in messages
            if item.get("sender_type") == "admin"
            and isinstance(item.get("id"), str)
            and item["id"] not in session.known_message_ids
        ]

        if new_admin_messages:
            lines = [format_status_message_line(item) for item in new_admin_messages]
            await context.bot.send_message(
                chat_id=chat_id,
                text="New reply:\n" + "\n".join(lines),
            )
            await deliver_live_admin_messages(
                context,
                chat_id=chat_id,
                api=api,
                token=token,
                messages=new_admin_messages,
            )

        active_session = registry.get(chat_id)
        if active_session is None:
            continue
        active_session.known_message_ids.update(
            message_id
            for item in messages
            if isinstance((message_id := item.get("id")), str)
            and message_id
        )
