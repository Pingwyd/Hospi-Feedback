"""Tests for inbound photo session preferences."""

from __future__ import annotations

from bot.constants import (
    STATUS_PHOTO_INBOUND_QUEUE_KEY,
    STATUS_PHOTO_JPEG_QUALITY_KEY,
    STATUS_PHOTO_VIEW_HIDE,
    STATUS_PHOTO_VIEW_MODE_KEY,
    STATUS_PHOTO_VIEW_SHOW,
)
from bot.constants import STATUS_PHOTO_LAST_INBOUND_BATCH_KEY
from bot.inbound_photo_delivery import (
    clear_inbound_photo_prefs,
    clear_inbound_ticket_photo_state,
    extend_inbound_photo_queue,
    inbound_photo_jpeg_quality,
    inbound_photo_view_mode,
    inbound_photos_for_ticket_resend,
    last_inbound_photo_batch,
    merge_inbound_photo_items,
    pop_inbound_photo_queue,
    set_last_inbound_photo_batch,
)


def test_clear_inbound_photo_prefs_removes_session_keys() -> None:
    user_data = {
        STATUS_PHOTO_VIEW_MODE_KEY: STATUS_PHOTO_VIEW_SHOW,
        STATUS_PHOTO_JPEG_QUALITY_KEY: 90,
        STATUS_PHOTO_INBOUND_QUEUE_KEY: [{"caption": "x", "preview_url": "/a"}],
    }
    clear_inbound_photo_prefs(user_data)
    assert STATUS_PHOTO_VIEW_MODE_KEY not in user_data
    assert STATUS_PHOTO_JPEG_QUALITY_KEY not in user_data
    assert STATUS_PHOTO_INBOUND_QUEUE_KEY not in user_data


def test_queue_deduplicates_preview_urls() -> None:
    user_data: dict = {}
    extend_inbound_photo_queue(
        user_data,
        [("One", "/api/x/1"), ("Two", "/api/x/1")],
    )
    queue = pop_inbound_photo_queue(user_data)
    assert len(queue) == 1
    assert queue[0]["preview_url"] == "/api/x/1"


def test_hide_mode_and_default_quality() -> None:
    user_data = {STATUS_PHOTO_VIEW_MODE_KEY: STATUS_PHOTO_VIEW_HIDE}
    assert inbound_photo_view_mode(user_data) == STATUS_PHOTO_VIEW_HIDE
    assert inbound_photo_jpeg_quality(user_data) == 70
    user_data[STATUS_PHOTO_JPEG_QUALITY_KEY] = 50
    assert inbound_photo_jpeg_quality(user_data) == 50


def test_ticket_photo_state_clear_keeps_quality() -> None:
    user_data = {
        STATUS_PHOTO_JPEG_QUALITY_KEY: 90,
        STATUS_PHOTO_VIEW_MODE_KEY: STATUS_PHOTO_VIEW_SHOW,
    }
    clear_inbound_ticket_photo_state(user_data)
    assert user_data[STATUS_PHOTO_JPEG_QUALITY_KEY] == 90
    assert STATUS_PHOTO_VIEW_MODE_KEY not in user_data


def test_merge_inbound_photo_items_dedupes_urls() -> None:
    merged = merge_inbound_photo_items(
        [{"caption": "A", "preview_url": "/1"}],
        [{"caption": "B", "preview_url": "/1"}, {"caption": "C", "preview_url": "/2"}],
    )
    assert len(merged) == 2
    assert merged[0]["preview_url"] == "/1"
    assert merged[1]["preview_url"] == "/2"


def test_set_last_inbound_batch_accumulates_per_session() -> None:
    user_data: dict = {}
    set_last_inbound_photo_batch(
        user_data,
        [{"caption": "First", "preview_url": "/a"}],
    )
    set_last_inbound_photo_batch(
        user_data,
        [{"caption": "Second", "preview_url": "/b"}],
    )
    assert len(last_inbound_photo_batch(user_data)) == 2


def test_inbound_photos_for_ticket_resend_includes_queue() -> None:
    user_data: dict = {}
    set_last_inbound_photo_batch(
        user_data,
        [{"caption": "Sent", "preview_url": "/sent"}],
    )
    extend_inbound_photo_queue(user_data, [("Queued", "/queued")])
    items = inbound_photos_for_ticket_resend(user_data)
    assert len(items) == 2


def test_last_inbound_batch_cleared_with_prefs() -> None:
    user_data: dict = {}
    set_last_inbound_photo_batch(
        user_data,
        [{"caption": "Admin photo", "preview_url": "/api/x/1"}],
    )
    assert len(last_inbound_photo_batch(user_data)) == 1
    clear_inbound_photo_prefs(user_data)
    assert STATUS_PHOTO_LAST_INBOUND_BATCH_KEY not in user_data
