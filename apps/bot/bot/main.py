"""Telegram bot entrypoint: polling (local/staging) or webhook (production)."""

from __future__ import annotations

import logging
import os

from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from bot.api_client import HospiApiClient
from bot.config import BotSettings, get_settings
from bot.constants import (
    ACCESS_CODE,
    DELETE_CALLBACK_PREFIX,
    MENU_CALLBACK_PREFIX,
    REPORT_CALLBACK_PREFIX,
    REPORT_CONFIRM,
    REPORT_DESCRIPTION,
    REPORT_MEMBER,
    REPORT_PHOTO,
    REPORT_SEVERITY,
    SKIP_CALLBACK,
    STATUS_AWAIT_CODE,
)
from bot.handlers.admin import link_command, stats_command
from bot.handlers.callbacks import delete_message_callback
from bot.handlers.menu import handle_menu_callback
from bot.handlers.report import (
    confirm_report,
    receive_description,
    receive_member_text,
    receive_photo,
    receive_severity,
    skip_member,
    skip_photo,
)
from bot.handlers.start import (
    cancel_command,
    help_command,
    receive_access_code,
    start_command,
)
from bot.handlers.status import receive_status_code, status_chat_message, status_command

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

_ALLOWED_UPDATES = ["message", "callback_query"]


def build_application(settings: BotSettings) -> Application:
    application = Application.builder().token(settings.telegram_bot_token).build()
    application.bot_data["api_client"] = HospiApiClient(
        base_url=settings.api_base_url,
        bot_service_secret=settings.bot_service_secret,
    )
    application.bot_data["settings"] = settings

    reporter_conv = ConversationHandler(
        entry_points=[
            CommandHandler("start", start_command),
            CallbackQueryHandler(
                handle_menu_callback,
                pattern=rf"^{MENU_CALLBACK_PREFIX}",
            ),
        ],
        states={
            ACCESS_CODE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    receive_access_code,
                )
            ],
            REPORT_DESCRIPTION: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    receive_description,
                )
            ],
            REPORT_MEMBER: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    receive_member_text,
                ),
                CallbackQueryHandler(skip_member, pattern=f"^{SKIP_CALLBACK}$"),
            ],
            REPORT_SEVERITY: [
                CallbackQueryHandler(
                    receive_severity,
                    pattern=rf"^({REPORT_CALLBACK_PREFIX}(low|medium|high)|{SKIP_CALLBACK})$",
                )
            ],
            REPORT_PHOTO: [
                MessageHandler(filters.PHOTO, receive_photo),
                CallbackQueryHandler(skip_photo, pattern=f"^{SKIP_CALLBACK}$"),
            ],
            REPORT_CONFIRM: [
                CallbackQueryHandler(
                    confirm_report,
                    pattern=r"^confirm:(submit|cancel)$",
                )
            ],
            STATUS_AWAIT_CODE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    receive_status_code,
                )
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_command),
            CommandHandler("start", start_command),
            CommandHandler("help", help_command),
        ],
        allow_reentry=True,
    )

    application.add_handler(reporter_conv)
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("link", link_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(
        CallbackQueryHandler(
            delete_message_callback,
            pattern=rf"^{DELETE_CALLBACK_PREFIX}\d+$",
        )
    )
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            status_chat_message,
        ),
        group=1,
    )
    return application


def _webhook_listen_port() -> int:
    raw = os.environ.get("PORT", "8080").strip()
    try:
        return int(raw)
    except ValueError:
        return 8080


def _run_polling(application: Application, settings: BotSettings) -> None:
    logger.info("Starting bot in polling mode against %s", settings.api_base_url)
    application.run_polling(allowed_updates=_ALLOWED_UPDATES)


def _run_webhook(application: Application, settings: BotSettings) -> None:
    base_url = settings.webhook_base_url.strip().rstrip("/")
    if not base_url:
        raise SystemExit(
            "WEBHOOK_BASE_URL is required when BOT_MODE=webhook. "
            "Do not deploy webhook mode until cutover is approved."
        )
    path = settings.webhook_path.strip().strip("/") or "telegram-webhook"
    port = _webhook_listen_port()
    webhook_url = f"{base_url}/{path}"
    logger.info("Starting bot in webhook mode at %s (port %s)", webhook_url, port)
    application.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=path,
        webhook_url=webhook_url,
        allowed_updates=_ALLOWED_UPDATES,
    )


def main() -> None:
    settings = get_settings()
    mode = settings.bot_mode.strip().lower()
    application = build_application(settings)
    if mode == "polling":
        _run_polling(application, settings)
        return
    if mode == "webhook":
        _run_webhook(application, settings)
        return
    raise SystemExit(f"Unsupported BOT_MODE: {settings.bot_mode!r}")


if __name__ == "__main__":
    main()
