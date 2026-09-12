"""Tests for /stats error mapping, text formatting, and cache."""

from __future__ import annotations

import pytest
from bot.api_client import ApiClientError
from bot.handlers.admin import map_stats_api_error
from bot.handlers.stats_text import format_dashboard_stats_text
from bot.stats_cache import (
    STATS_CACHE_TTL_SECONDS,
    clear_stats_cache,
    get_cached_stats,
    set_cached_stats,
)


def test_map_stats_api_error_unlinked() -> None:
    exc = ApiClientError(
        403,
        "forbidden",
        "No linked admin account matches this Telegram chat.",
    )
    message = map_stats_api_error(exc)
    assert "/link" in message


def test_map_stats_api_error_permission() -> None:
    exc = ApiClientError(
        403,
        "forbidden",
        "Permission 'view' is required for this action.",
    )
    message = map_stats_api_error(exc)
    assert "view permission" in message
    assert "/link" not in message


def test_map_stats_api_error_transient() -> None:
    exc = ApiClientError(500, "error", "Server error.")
    assert "Try again" in map_stats_api_error(exc)


def test_format_dashboard_stats_text_omits_report_id() -> None:
    text = format_dashboard_stats_text(
        {
            "status_counts": {"new": 2, "closed": 1},
            "submissions_by_day": [{"date": "2026-09-10", "count": 3}],
            "oldest_unresolved": {
                "report_id": "rep_secret_should_not_appear",
                "status": "new",
                "created_at": "2026-09-01T12:00:00+00:00",
            },
            "system_alerts": [],
        }
    )
    assert "rep_secret_should_not_appear" not in text
    assert "Status breakdown:" in text
    assert "Oldest unresolved:" in text
    assert "Overview:" in text


def test_stats_cache_expires(monkeypatch: pytest.MonkeyPatch) -> None:
    clear_stats_cache()
    current = 0.0

    def monotonic() -> float:
        return current

    monkeypatch.setattr("bot.stats_cache.time.monotonic", monotonic)
    set_cached_stats("123", {"status_counts": {"new": 1}})
    assert get_cached_stats("123") is not None

    current = STATS_CACHE_TTL_SECONDS + 1
    assert get_cached_stats("123") is None
