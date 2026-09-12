"""Admin bot commands."""

from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from bot.api_client import ApiClientError, HospiApiClient
from bot.config import BotSettings
from bot.handlers.stats_delivery import deliver_stats_message
from bot.stats_cache import get_cached_stats, set_cached_stats

MSG_STATS_UNLINKED = (
    "Your Telegram account is not linked to an admin profile. "
    "Run /link with a one-time code from the admin dashboard."
)
MSG_STATS_NO_PERMISSION = (
    "Your admin account does not have dashboard view permission. "
    "Ask the Head of Hospi to grant view access."
)
MSG_STATS_CONFIG = (
    "Stats are temporarily unavailable (service configuration). "
    "Contact the platform operator."
)
MSG_STATS_TRANSIENT = "Could not load dashboard stats right now. Try again in a moment."


def map_stats_api_error(exc: ApiClientError) -> str:
    if exc.status_code == 403:
        if "No linked admin account" in exc.message:
            return MSG_STATS_UNLINKED
        if "Permission 'view'" in exc.message:
            return MSG_STATS_NO_PERMISSION
        return MSG_STATS_NO_PERMISSION
    if exc.status_code in {401, 503}:
        return MSG_STATS_CONFIG
    return MSG_STATS_TRANSIENT


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
    if update.message is None or update.effective_chat is None:
        return

    settings: BotSettings = context.application.bot_data["settings"]
    if not settings.bot_service_secret.strip():
        await update.message.reply_text(MSG_STATS_CONFIG)
        return

    chat_id = str(update.effective_chat.id)
    cached = get_cached_stats(chat_id)
    if cached is not None:
        await deliver_stats_message(update, cached, settings=settings)
        return

    api: HospiApiClient = context.application.bot_data["api_client"]
    try:
        stats_payload = await api.fetch_telegram_dashboard_stats(
            telegram_chat_id=chat_id,
        )
    except ApiClientError as exc:
        await update.message.reply_text(map_stats_api_error(exc))
        return

    set_cached_stats(chat_id, stats_payload)
    await deliver_stats_message(update, stats_payload, settings=settings)
