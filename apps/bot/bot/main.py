"""Telegram bot entrypoint (polling in local/staging)."""

from __future__ import annotations

import logging

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


def main() -> None:
    settings = get_settings()
    if settings.bot_mode.strip().lower() != "polling":
        raise SystemExit("Only polling mode is supported in this phase.")
    application = build_application(settings)
    logger.info("Starting bot in polling mode against %s", settings.api_base_url)
    application.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
