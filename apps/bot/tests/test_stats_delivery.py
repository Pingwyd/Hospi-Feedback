"""Tests for /stats delivery modes and image-to-text fallback."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bot.config import BotSettings
from bot.handlers.stats_delivery import deliver_stats_message
from bot.handlers.stats_image import deliver_stats_image


@pytest.mark.asyncio
async def test_deliver_stats_message_text_mode() -> None:
    update = MagicMock()
    update.message = AsyncMock()
    settings = BotSettings(
        telegram_bot_token="token",
        telegram_identifier_pepper="pepper",
        stats_render_mode="text",
    )
    payload = {"status_counts": {"new": 1}, "submissions_by_day": []}

    await deliver_stats_message(update, payload, settings=settings)

    update.message.reply_text.assert_awaited_once()
    update.message.reply_photo.assert_not_called()


@pytest.mark.asyncio
async def test_deliver_stats_message_image_mode_sends_photo() -> None:
    update = MagicMock()
    update.message = AsyncMock()
    settings = BotSettings(
        telegram_bot_token="token",
        telegram_identifier_pepper="pepper",
        stats_render_mode="image",
    )
    payload = {
        "status_counts": {"new": 2},
        "submissions_by_day": [{"date": "2026-09-10", "count": 2}],
    }

    await deliver_stats_message(update, payload, settings=settings)

    update.message.reply_photo.assert_awaited_once()
    update.message.reply_text.assert_not_called()


@pytest.mark.asyncio
async def test_deliver_stats_message_image_mode_falls_back_on_render_error() -> None:
    update = MagicMock()
    update.message = AsyncMock()
    settings = BotSettings(
        telegram_bot_token="token",
        telegram_identifier_pepper="pepper",
        stats_render_mode="image",
    )
    payload = {"status_counts": {"new": 1}, "submissions_by_day": []}

    with patch(
        "bot.handlers.stats_image.deliver_stats_image",
        new=AsyncMock(side_effect=RuntimeError("render failed")),
    ):
        await deliver_stats_message(update, payload, settings=settings)

    update.message.reply_text.assert_awaited_once()
    text = update.message.reply_text.await_args.args[0]
    assert "Status breakdown:" in text


@pytest.mark.asyncio
async def test_deliver_stats_image_rejects_empty_status_counts() -> None:
    update = MagicMock()
    update.message = AsyncMock()

    empty_payload = {"status_counts": {}, "submissions_by_day": []}
    with pytest.raises(ValueError, match="No chart data"):
        await deliver_stats_image(update, empty_payload)
