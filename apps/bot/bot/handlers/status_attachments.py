"""Attachment preview helpers for Telegram status display."""

from __future__ import annotations

from typing import Any

PHOTO_PLACEHOLDER = "Photo attached"


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
        attachment = message.get("attachment")
        if not isinstance(attachment, dict):
            continue
        preview_url = attachment.get("preview_url")
        if not isinstance(preview_url, str) or not preview_url.strip():
            continue
        sender = str(message.get("sender_type") or "unknown")
        items.append((f"Follow-up photo ({sender})", preview_url))
    return items
