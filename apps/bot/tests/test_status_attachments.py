"""Tests for Telegram status attachment preview helpers."""

from __future__ import annotations

from bot.handlers.status import format_ticket_status
from bot.handlers.status_attachments import (
    PHOTO_PLACEHOLDER,
    iter_status_attachment_previews,
)


def test_iter_status_attachment_previews_orders_report_then_messages() -> None:
    payload = {
        "report_attachments": [
            {"preview_url": "/api/reports/ticket/ABCD1234/attachments/a1"},
        ],
        "messages": [
            {
                "sender_type": "reporter",
                "content": PHOTO_PLACEHOLDER,
                "attachment": {
                    "preview_url": "/api/reports/ticket/ABCD1234/attachments/a2",
                },
            },
            {
                "sender_type": "admin",
                "content": "We are reviewing this.",
            },
        ],
    }
    items = iter_status_attachment_previews(payload)
    assert len(items) == 2
    assert items[0] == (
        "Original report photo",
        "/api/reports/ticket/ABCD1234/attachments/a1",
    )
    assert items[1][0] == "Follow-up photo (reporter)"
    assert items[1][1].endswith("/attachments/a2")


def test_format_ticket_status_marks_photo_messages() -> None:
    payload = {
        "status": "new",
        "report_type": "complaint",
        "description": "Test",
        "messages": [
            {
                "sender_type": "reporter",
                "content": PHOTO_PLACEHOLDER,
                "attachment": {"preview_url": "/x"},
            }
        ],
    }
    text = format_ticket_status(payload)
    assert "[photo attached below]" in text
    assert PHOTO_PLACEHOLDER not in text.split("Messages:")[1]
