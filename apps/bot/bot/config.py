"""Process settings for the Telegram bot."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

StatsRenderMode = Literal["text", "image"]

# Lookup by path: pydantic-settings resolves a relative env_file against cwd,
# so `python -m bot.main` from apps/bot/bot would miss apps/bot/.env.
_BOT_APP_DIR = Path(__file__).resolve().parent.parent
_ENV_FILE = _BOT_APP_DIR / ".env"


class BotSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    telegram_bot_token: str
    api_base_url: str = "http://127.0.0.1:8000"
    telegram_identifier_pepper: str
    bot_service_secret: str = ""
    stats_render_mode: StatsRenderMode = "text"
    bot_mode: str = "polling"
    webhook_base_url: str = ""
    webhook_path: str = "telegram-webhook"


@lru_cache
def get_settings() -> BotSettings:
    return BotSettings()
