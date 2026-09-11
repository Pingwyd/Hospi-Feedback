"""Telegram Bot API helpers for internal job notifications."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
import uuid
from typing import Any

from app.exceptions.base import AppError


class TelegramNotifyError(AppError):
    """Telegram Bot API call failed."""


def _multipart_body(
    *,
    fields: dict[str, str],
    file_field: str,
    filename: str,
    content: bytes,
    content_type: str,
) -> tuple[bytes, str]:
    boundary = uuid.uuid4().hex
    lines: list[bytes] = []
    for name, value in fields.items():
        lines.append(f"--{boundary}\r\n".encode())
        lines.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        lines.append(f"{value}\r\n".encode())
    lines.append(f"--{boundary}\r\n".encode())
    lines.append(
        (
            f'Content-Disposition: form-data; name="{file_field}"; '
            f'filename="{filename}"\r\n'
        ).encode()
    )
    lines.append(f"Content-Type: {content_type}\r\n\r\n".encode())
    lines.append(content)
    lines.append(b"\r\n")
    lines.append(f"--{boundary}--\r\n".encode())
    body = b"".join(lines)
    content_type_header = f"multipart/form-data; boundary={boundary}"
    return body, content_type_header


def send_telegram_document(
    *,
    bot_token: str,
    chat_id: str,
    filename: str,
    content: bytes,
    caption: str | None = None,
) -> dict[str, Any]:
    token = bot_token.strip()
    if not token:
        raise TelegramNotifyError("Telegram bot token is not configured.")
    fields: dict[str, str] = {"chat_id": chat_id}
    if caption:
        fields["caption"] = caption
    body, content_type = _multipart_body(
        fields=fields,
        file_field="document",
        filename=filename,
        content=content,
        content_type="application/pdf",
    )
    url = f"https://api.telegram.org/bot{token}/sendDocument"
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": content_type},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise TelegramNotifyError(
            f"Telegram sendDocument failed with HTTP {exc.code}.",
            context={"status": exc.code, "detail": detail},
        ) from exc
    except urllib.error.URLError as exc:
        raise TelegramNotifyError(
            "Telegram sendDocument could not connect.",
            context={"reason": str(exc.reason)},
        ) from exc
    if not payload.get("ok"):
        raise TelegramNotifyError(
            "Telegram sendDocument returned ok=false.",
            context={"description": payload.get("description")},
        )
    return payload
