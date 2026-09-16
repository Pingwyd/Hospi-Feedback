"""Session-scoped inbound photo view preferences and delivery queue."""

from __future__ import annotations

from typing import Any

from bot.constants import (
    DEFAULT_INBOUND_PHOTO_JPEG_QUALITY,
    STATUS_PHOTO_INBOUND_QUEUE_KEY,
    STATUS_PHOTO_JPEG_QUALITY_KEY,
    STATUS_PHOTO_LAST_INBOUND_BATCH_KEY,
    STATUS_PHOTO_AWAITING_SHOW_QUALITY_KEY,
    STATUS_PHOTO_PROMPT_MSG_ID_KEY,
    STATUS_PHOTO_VIEW_HIDE,
    STATUS_PHOTO_VIEW_MODE_KEY,
    STATUS_PHOTO_VIEW_SHOW,
)

InboundPhotoItem = dict[str, str]


def clear_inbound_ticket_photo_state(user_data: dict[str, Any]) -> None:
    """Per-ticket photo view state (queue, show/hide, last batch). Keeps quality."""
    user_data.pop(STATUS_PHOTO_VIEW_MODE_KEY, None)
    user_data.pop(STATUS_PHOTO_INBOUND_QUEUE_KEY, None)
    user_data.pop(STATUS_PHOTO_PROMPT_MSG_ID_KEY, None)
    user_data.pop(STATUS_PHOTO_AWAITING_SHOW_QUALITY_KEY, None)
    user_data.pop(STATUS_PHOTO_LAST_INBOUND_BATCH_KEY, None)


def clear_inbound_photo_prefs(user_data: dict[str, Any]) -> None:
    """Full inbound photo prefs, including quality (access session teardown)."""
    clear_inbound_ticket_photo_state(user_data)
    user_data.pop(STATUS_PHOTO_JPEG_QUALITY_KEY, None)


def inbound_photo_view_mode(user_data: dict[str, Any]) -> str | None:
    mode = user_data.get(STATUS_PHOTO_VIEW_MODE_KEY)
    if mode in {STATUS_PHOTO_VIEW_SHOW, STATUS_PHOTO_VIEW_HIDE}:
        return mode
    return None


def inbound_photo_jpeg_quality(user_data: dict[str, Any]) -> int:
    raw = user_data.get(STATUS_PHOTO_JPEG_QUALITY_KEY)
    if raw in {50, 70, 90}:
        return int(raw)
    return DEFAULT_INBOUND_PHOTO_JPEG_QUALITY


def inbound_photo_queue(user_data: dict[str, Any]) -> list[InboundPhotoItem]:
    return inbound_photo_queue_from_key(user_data, STATUS_PHOTO_INBOUND_QUEUE_KEY)


def inbound_photo_queue_from_key(
    user_data: dict[str, Any],
    key: str,
) -> list[InboundPhotoItem]:
    raw = user_data.get(key)
    if not isinstance(raw, list):
        return []
    items: list[InboundPhotoItem] = []
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        caption = entry.get("caption")
        preview_url = entry.get("preview_url")
        if isinstance(caption, str) and isinstance(preview_url, str) and preview_url:
            items.append({"caption": caption, "preview_url": preview_url})
    return items


def extend_inbound_photo_queue(
    user_data: dict[str, Any],
    items: list[tuple[str, str]],
) -> None:
    if not items:
        return
    queue = inbound_photo_queue(user_data)
    existing_urls = {item["preview_url"] for item in queue}
    for caption, preview_url in items:
        if preview_url in existing_urls:
            continue
        queue.append({"caption": caption, "preview_url": preview_url})
        existing_urls.add(preview_url)
    user_data[STATUS_PHOTO_INBOUND_QUEUE_KEY] = queue


def pop_inbound_photo_queue(user_data: dict[str, Any]) -> list[InboundPhotoItem]:
    queue = inbound_photo_queue(user_data)
    user_data.pop(STATUS_PHOTO_INBOUND_QUEUE_KEY, None)
    return queue


def last_inbound_photo_batch(user_data: dict[str, Any]) -> list[InboundPhotoItem]:
    return inbound_photo_queue_from_key(user_data, STATUS_PHOTO_LAST_INBOUND_BATCH_KEY)


def merge_inbound_photo_items(
    *groups: list[InboundPhotoItem],
) -> list[InboundPhotoItem]:
    """Dedupe by preview_url; order preserved across groups."""
    merged: list[InboundPhotoItem] = []
    seen_urls: set[str] = set()
    for group in groups:
        for item in group:
            preview_url = item.get("preview_url")
            if not isinstance(preview_url, str) or not preview_url:
                continue
            if preview_url in seen_urls:
                continue
            caption = item.get("caption")
            if not isinstance(caption, str):
                caption = ""
            merged.append({"caption": caption, "preview_url": preview_url})
            seen_urls.add(preview_url)
    return merged


def set_last_inbound_photo_batch(
    user_data: dict[str, Any],
    items: list[InboundPhotoItem],
) -> None:
    if not items:
        return
    user_data[STATUS_PHOTO_LAST_INBOUND_BATCH_KEY] = merge_inbound_photo_items(
        last_inbound_photo_batch(user_data),
        items,
    )


def inbound_photos_for_ticket_resend(user_data: dict[str, Any]) -> list[InboundPhotoItem]:
    """Photos already sent this ticket session plus any still queued."""
    return merge_inbound_photo_items(
        last_inbound_photo_batch(user_data),
        inbound_photo_queue(user_data),
    )
