"""Process settings for the Telegram bot."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

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
    bot_mode: str = "polling"


@lru_cache
def get_settings() -> BotSettings:
    return BotSettings()
