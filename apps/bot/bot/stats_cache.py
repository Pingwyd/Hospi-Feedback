"""Short-lived in-memory cache for /stats API responses."""

from __future__ import annotations

import time
from typing import Any

STATS_CACHE_TTL_SECONDS = 90

_cache: dict[str, tuple[float, dict[str, Any]]] = {}


def get_cached_stats(chat_id: str) -> dict[str, Any] | None:
    entry = _cache.get(chat_id)
    if entry is None:
        return None
    fetched_at, payload = entry
    if time.monotonic() - fetched_at > STATS_CACHE_TTL_SECONDS:
        _cache.pop(chat_id, None)
        return None
    return payload


def set_cached_stats(chat_id: str, payload: dict[str, Any]) -> None:
    _cache[chat_id] = (time.monotonic(), payload)


def clear_stats_cache() -> None:
    _cache.clear()
