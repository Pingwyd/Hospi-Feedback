"""Conversation states and callback prefixes."""

from __future__ import annotations

ACCESS_CODE = 1
REPORT_DESCRIPTION = 2
REPORT_MEMBER = 3
REPORT_SEVERITY = 4
REPORT_PHOTO = 5
REPORT_CONFIRM = 6
STATUS_AWAIT_CODE = 7
MENU_DISCARD_CONFIRM = 8

DELETE_CALLBACK_PREFIX = "delmsg:"
MENU_CALLBACK_PREFIX = "menu:"
MENU_GO_CALLBACK_PREFIX = "menu_go:"
MENU_KEEP_CALLBACK = "menu_keep"
REPORT_CALLBACK_PREFIX = "report:"
SKIP_CALLBACK = "skip"
CONFIRM_SUBMIT = "confirm:submit"
CONFIRM_CANCEL = "confirm:cancel"

SESSION_TOKEN_KEY = "access_token"
SESSION_EXPIRES_KEY = "access_expires_at"
REPORT_DRAFT_KEY = "report_draft"
REPORT_FLOW_STATE_KEY = "report_flow_state"
STATUS_TICKET_KEY = "status_ticket_code"
DELETE_TARGETS_KEY = "delete_targets"
PERSISTENT_KEYBOARD_ATTACHED_KEY = "persistent_keyboard_attached"

PERSISTENT_MENU_LABEL = "Menu"
PERSISTENT_CANCEL_LABEL = "Cancel"

SESSION_EXPIRED_ACCESS_CODE_MSG = (
    "Your session expired. Enter your access code to continue."
)
DISCARD_REPORT_CONFIRM_MSG = "You have a report in progress. Discard it and continue?"

TICKET_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
TICKET_CODE_LENGTH = 8

DELETE_BUTTON_LABEL = "🗑️ Delete this message"

PRIVACY_NOTICE = (
    "Privacy notice:\n"
    "- We do not ask for your name or login. Your report cannot be traced "
    "back to you.\n"
    "- Your ticket code is the only way to return to this thread. We cannot "
    "recover it if you lose it.\n"
    "- On Telegram, your chat id is hashed for rate limiting only. It is "
    "never shown to admins and never linked to report content.\n"
    "- Admins who link Telegram store an encrypted chat id for pushes. That "
    "is separate from reporter anonymity.\n"
    "- If your bot session ends, admin replies will not push to you. Run "
    "/status with your ticket code to read replies."
)

HELP_TEXT = (
    "Hospi Feedback bot\n\n"
    "Reporter commands:\n"
    "/start - enter access code and open the main menu\n"
    "/menu - show the main menu again\n"
    "/status <code> - check a ticket and chat with admins\n"
    "/cancel - stop the current flow\n"
    "/help - show this message\n\n"
    "Save your ticket code somewhere safe. Anyone with the code can read "
    "that thread."
)

STATUS_ASYNC_NOTE = (
    "Note: if your session ends, new admin replies will not push here. "
    "Run /status with your ticket code again to read them."
)
