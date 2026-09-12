"""Deliver /stats output in text or image mode with automatic fallback."""

from __future__ import annotations

import logging

from telegram import Update

from bot.config import BotSettings
from bot.handlers.stats_text import format_dashboard_stats_text

logger = logging.getLogger(__name__)


async def deliver_stats_message(
    update: Update,
    payload: dict,
    *,
    settings: BotSettings,
) -> None:
    if update.message is None:
        return

    mode = settings.stats_render_mode
    if mode == "image":
        try:
            from bot.handlers.stats_image import deliver_stats_image

            await deliver_stats_image(update, payload)
            return
        except Exception:
            logger.exception("stats_image_render_failed")

    await update.message.reply_text(format_dashboard_stats_text(payload))
