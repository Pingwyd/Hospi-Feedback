"""Attachment preview helpers for Telegram status display."""

from __future__ import annotations

from typing import Any

PHOTO_PLACEHOLDER = "Photo attached"


def _attachment_dicts_for_message(message: dict) -> list[dict]:
    attachments = message.get("attachments")
    if isinstance(attachments, list) and attachments:
        return [item for item in attachments if isinstance(item, dict)]
    attachment = message.get("attachment")
    if isinstance(attachment, dict):
        return [attachment]
    return []


def iter_message_attachment_previews(message: dict) -> list[tuple[str, str]]:
    """Return (caption, preview_url) pairs for one thread message."""
    sender = str(message.get("sender_type") or "unknown")
    items: list[tuple[str, str]] = []
    attachments = _attachment_dicts_for_message(message)
    for index, attachment in enumerate(attachments, start=1):
        preview_url = attachment.get("preview_url")
        if not isinstance(preview_url, str) or not preview_url.strip():
            continue
        label = f"Follow-up photo ({sender})"
        if len(attachments) > 1:
            label = f"{label} {index}"
        items.append((label, preview_url))
    return items


def iter_status_attachment_previews(
    payload: dict[str, Any],
) -> list[tuple[str, str]]:
    """Return ordered (caption, preview_url) pairs for sendPhoto delivery."""
    items: list[tuple[str, str]] = []
    for attachment in payload.get("report_attachments") or []:
        preview_url = attachment.get("preview_url")
        if isinstance(preview_url, str) and preview_url.strip():
            items.append(("Original report photo", preview_url))
    for message in payload.get("messages") or []:
        items.extend(iter_message_attachment_previews(message))
    return items
