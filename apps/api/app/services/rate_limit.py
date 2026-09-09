"""Rate limit checks for web fingerprints and Telegram identifier hashes."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Literal

from app.core.settings import Settings
from app.exceptions.rate_limit import RateLimitExceededError
from app.integrations.rate_limit_store import (
    fetch_entry_for_window,
    increment_entry,
    insert_entry,
)

RateLimitChannel = Literal["web", "telegram"]
IDENTIFIER_HASH_PATTERN = re.compile(r"^[a-f0-9]{64}$")


def _window_start(now: datetime, *, window_seconds: int) -> datetime:
    epoch = int(now.timestamp())
    aligned = epoch - (epoch % window_seconds)
    return datetime.fromtimestamp(aligned, tz=UTC)


def _store_kwargs(settings: Settings) -> dict[str, str]:
    return {
        "supabase_url": settings.supabase_url,
        "service_role_key": settings.supabase_service_role_key,
    }


def check_and_record_rate_limit(
    *,
    channel: RateLimitChannel,
    identifier_hash: str,
    settings: Settings,
) -> None:
    normalized = identifier_hash.strip().lower()
    if not IDENTIFIER_HASH_PATTERN.fullmatch(normalized):
        raise RateLimitExceededError("Invalid rate limit identifier.")
    now = datetime.now(tz=UTC)
    window_start = _window_start(now, window_seconds=settings.rate_limit_window_seconds)
    existing = fetch_entry_for_window(
        **_store_kwargs(settings),
        channel=channel,
        identifier_hash=normalized,
        window_start=window_start,
    )
    if existing is None:
        insert_entry(
            **_store_kwargs(settings),
            channel=channel,
            identifier_hash=normalized,
            window_start=window_start,
        )
        return
    current_count = int(existing.get("request_count") or 0)
    if current_count >= settings.rate_limit_max_requests:
        raise RateLimitExceededError("Rate limit exceeded. Try again later.")
    increment_entry(
        **_store_kwargs(settings),
        entry_id=str(existing["id"]),
        request_count=current_count + 1,
    )
