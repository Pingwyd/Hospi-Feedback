"""Register a deletable bot message for the delete-message callback."""

from __future__ import annotations

from typing import Any

from bot.constants import DELETE_TARGETS_KEY


def register_delete_target(
    user_data: dict[str, Any], *, chat_id: int, message_id: int
) -> None:
    targets = user_data.setdefault(DELETE_TARGETS_KEY, {})
    if not isinstance(targets, dict):
        targets = {}
        user_data[DELETE_TARGETS_KEY] = targets
    targets[message_id] = chat_id


def owns_delete_target(
    user_data: dict[str, Any], *, chat_id: int, message_id: int
) -> bool:
    targets = user_data.get(DELETE_TARGETS_KEY, {})
    if not isinstance(targets, dict):
        return False
    return targets.get(message_id) == chat_id
