"""Telegram inline keyboards."""

from __future__ import annotations

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

from bot.constants import (
    CONFIRM_CANCEL,
    CONFIRM_SUBMIT,
    DELETE_BUTTON_LABEL,
    DELETE_CALLBACK_PREFIX,
    MENU_CALLBACK_PREFIX,
    MENU_GO_CALLBACK_PREFIX,
    MENU_KEEP_CALLBACK,
    PERSISTENT_CANCEL_LABEL,
    PERSISTENT_MENU_LABEL,
    REPORT_CALLBACK_PREFIX,
    SKIP_CALLBACK,
)


def persistent_reply_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [
                KeyboardButton(PERSISTENT_MENU_LABEL),
                KeyboardButton(PERSISTENT_CANCEL_LABEL),
            ]
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


def remove_persistent_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "Report Concern",
                    callback_data=f"{MENU_CALLBACK_PREFIX}complaint",
                )
            ],
            [
                InlineKeyboardButton(
                    "Suggest Something",
                    callback_data=f"{MENU_CALLBACK_PREFIX}suggestion",
                )
            ],
            [
                InlineKeyboardButton(
                    "Shoutout",
                    callback_data=f"{MENU_CALLBACK_PREFIX}recognition",
                )
            ],
            [
                InlineKeyboardButton(
                    "Check Ticket Status",
                    callback_data=f"{MENU_CALLBACK_PREFIX}status",
                )
            ],
            [InlineKeyboardButton("Help", callback_data=f"{MENU_CALLBACK_PREFIX}help")],
        ]
    )


def skip_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("Skip", callback_data=SKIP_CALLBACK)]]
    )


def severity_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "Low", callback_data=f"{REPORT_CALLBACK_PREFIX}low"
                ),
                InlineKeyboardButton(
                    "Medium", callback_data=f"{REPORT_CALLBACK_PREFIX}medium"
                ),
                InlineKeyboardButton(
                    "High", callback_data=f"{REPORT_CALLBACK_PREFIX}high"
                ),
            ],
            [InlineKeyboardButton("Skip", callback_data=SKIP_CALLBACK)],
        ]
    )


def confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Submit report", callback_data=CONFIRM_SUBMIT),
                InlineKeyboardButton("Cancel", callback_data=CONFIRM_CANCEL),
            ]
        ]
    )


def discard_confirm_keyboard(action: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "Discard and continue",
                    callback_data=f"{MENU_GO_CALLBACK_PREFIX}{action}",
                )
            ],
            [InlineKeyboardButton("Keep report", callback_data=MENU_KEEP_CALLBACK)],
        ]
    )


def delete_message_keyboard(message_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    DELETE_BUTTON_LABEL,
                    callback_data=f"{DELETE_CALLBACK_PREFIX}{message_id}",
                )
            ]
        ]
    )
