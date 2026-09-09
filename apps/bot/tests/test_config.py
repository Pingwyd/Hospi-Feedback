"""Bot settings load from apps/bot/.env, not the process cwd."""

from pathlib import Path

from bot.config import _BOT_APP_DIR, _ENV_FILE, BotSettings


def test_env_file_is_bot_app_dotenv() -> None:
    assert _ENV_FILE.is_absolute()
    assert _ENV_FILE == _BOT_APP_DIR / ".env"
    assert _BOT_APP_DIR.name == "bot"
    assert BotSettings.model_config["env_file"] == _ENV_FILE
    assert Path(BotSettings.model_config["env_file"]).name == ".env"
