"""In-memory reporter session flags shared across bot handlers."""

from __future__ import annotations

from typing import Any

from bot.constants import (
    AWAITING_ACCESS_CODE_KEY,
    AWAITING_STATUS_CODE_KEY,
    PERSISTENT_KEYBOARD_ATTACHED_KEY,
    REPORT_DRAFT_KEY,
    REPORT_FLOW_STATE_KEY,
    STATUS_TICKET_KEY,
)
from bot.sessions import has_valid_access_session

_DRAFT_PROGRESS_KEYS = frozenset(
    {"description", "reported_member_name", "severity", "photo_file_id"}
)


def set_awaiting_status_code(user_data: dict[str, Any]) -> None:
    user_data[AWAITING_STATUS_CODE_KEY] = True


def clear_awaiting_status_code(user_data: dict[str, Any]) -> None:
    user_data.pop(AWAITING_STATUS_CODE_KEY, None)


def set_awaiting_access_code(user_data: dict[str, Any]) -> None:
    user_data[AWAITING_ACCESS_CODE_KEY] = True


def clear_awaiting_access_code(user_data: dict[str, Any]) -> None:
    user_data.pop(AWAITING_ACCESS_CODE_KEY, None)


def _draft_has_progress(user_data: dict[str, Any]) -> bool:
    draft = user_data.get(REPORT_DRAFT_KEY)
    if not isinstance(draft, dict) or not draft:
        return False
    return bool(_DRAFT_PROGRESS_KEYS & draft.keys())


def _had_prior_authenticated_session(user_data: dict[str, Any]) -> bool:
    if user_data.get(PERSISTENT_KEYBOARD_ATTACHED_KEY):
        return True
    if isinstance(user_data.get(STATUS_TICKET_KEY), str):
        return True
    if user_data.get(AWAITING_STATUS_CODE_KEY):
        return True
    draft = user_data.get(REPORT_DRAFT_KEY)
    if isinstance(draft, dict) and draft:
        return True
    if user_data.get(REPORT_FLOW_STATE_KEY) is not None:
        return True
    return False


def is_idle_for_nudge(user_data: dict[str, Any]) -> bool:
    if not has_valid_access_session(user_data):
        return False
    if isinstance(user_data.get(STATUS_TICKET_KEY), str):
        return False
    if user_data.get(REPORT_FLOW_STATE_KEY) is not None:
        return False
    if _draft_has_progress(user_data):
        return False
    if user_data.get(AWAITING_STATUS_CODE_KEY):
        return False
    return True


def is_first_touch_for_nudge(user_data: dict[str, Any]) -> bool:
    if has_valid_access_session(user_data):
        return False
    if user_data.get(AWAITING_ACCESS_CODE_KEY):
        return False
    if _had_prior_authenticated_session(user_data):
        return False
    return True


def is_lapsed_session_for_nudge(user_data: dict[str, Any]) -> bool:
    if has_valid_access_session(user_data):
        return False
    if user_data.get(AWAITING_ACCESS_CODE_KEY):
        return False
    if user_data.get(REPORT_FLOW_STATE_KEY) is not None:
        return False
    if user_data.get(AWAITING_STATUS_CODE_KEY):
        return False
    return _had_prior_authenticated_session(user_data)
