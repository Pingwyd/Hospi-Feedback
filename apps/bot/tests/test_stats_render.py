"""Tests for Step 2 /stats rendering (text enrichment and chart PNG)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from bot.handlers.stats_image import deliver_stats_image, render_stats_chart_png
from bot.handlers.stats_summary import format_stats_caption
from bot.handlers.stats_text import format_dashboard_stats_text

SAMPLE_PAYLOAD = {
    "status_counts": {"new": 3, "escalated": 1, "closed": 2},
    "report_type_counts": {"complaint": 4, "suggestion": 2},
    "submissions_by_day": [
        {"date": "2026-09-08", "count": 1},
        {"date": "2026-09-09", "count": 2},
        {"date": "2026-09-10", "count": 4},
    ],
    "oldest_unresolved": {
        "report_id": "rep_hidden_from_output",
        "status": "new",
        "created_at": "2026-09-01T12:00:00+00:00",
    },
    "system_alerts": [{"message": "Purge PDF delivery failed."}],
}


def test_format_dashboard_stats_text_includes_overview_and_types() -> None:
    text = format_dashboard_stats_text(SAMPLE_PAYLOAD)
    assert "Overview:" in text
    assert "unresolved" in text
    assert "Report types:" in text
    assert "complaint: 4" in text
    assert "rep_hidden_from_output" not in text


def test_format_stats_caption_omits_report_id() -> None:
    caption = format_stats_caption(SAMPLE_PAYLOAD)
    assert "rep_hidden_from_output" not in caption
    assert "Hospi dashboard summary" in caption
    assert "Last 7 days:" in caption


def test_render_stats_chart_png_returns_png_bytes() -> None:
    png = render_stats_chart_png(SAMPLE_PAYLOAD)
    assert png.startswith(b"\x89PNG")


def test_render_stats_chart_png_rejects_empty_payload() -> None:
    with pytest.raises(ValueError, match="No chart data"):
        render_stats_chart_png({"status_counts": {}, "submissions_by_day": []})


@pytest.mark.asyncio
async def test_deliver_stats_image_sends_photo_with_caption() -> None:
    update = MagicMock()
    update.message = AsyncMock()
    await deliver_stats_image(update, SAMPLE_PAYLOAD)
    update.message.reply_photo.assert_awaited_once()
    kwargs = update.message.reply_photo.await_args.kwargs
    assert kwargs["caption"]
    assert "rep_hidden_from_output" not in kwargs["caption"]
