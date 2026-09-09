"""Admin bot commands."""

from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from bot.api_client import ApiClientError, HospiApiClient
from bot.config import BotSettings

STATS_UNAVAILABLE = (
    "Admin stats are not available yet. "
    "TODO(phase-6-step-2): wire /stats to GET /api/admin/dashboard/stats."
)


async def link_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or update.effective_chat is None:
        return
    if not context.args:
        await update.message.reply_text(
            "Usage: /link <one-time-code>\n\n"
            "Generate a code from the admin dashboard, then run this command "
            "once to link Telegram notifications to your admin account."
        )
        return
    settings: BotSettings = context.application.bot_data["settings"]
    if not settings.bot_service_secret.strip():
        await update.message.reply_text(
            "Bot service secret is not configured on the bot. "
            "Set BOT_SERVICE_SECRET in apps/bot/.env."
        )
        return
    api: HospiApiClient = context.application.bot_data["api_client"]
    one_time_code = context.args[0].strip()
    chat_id = str(update.effective_chat.id)
    try:
        await api.link_telegram_account(
            one_time_code=one_time_code,
            telegram_chat_id=chat_id,
        )
    except ApiClientError as exc:
        if exc.status_code == 401:
            await update.message.reply_text(
                "That link code is invalid or expired. "
                "Generate a new code from the admin dashboard."
            )
        else:
            await update.message.reply_text(
                "Could not link your Telegram account. Try again in a moment."
            )
        return
    await update.message.reply_text(
        "Your Telegram account is linked. "
        "You can receive admin notifications here when that feature is enabled."
    )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return
    await update.message.reply_text(STATS_UNAVAILABLE)
