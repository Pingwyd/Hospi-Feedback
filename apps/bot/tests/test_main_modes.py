"""Bot entrypoint mode validation."""

from unittest.mock import MagicMock

import pytest
from bot.config import BotSettings


def test_webhook_mode_requires_base_url() -> None:
    settings = BotSettings(
        telegram_bot_token="test-token",
        telegram_identifier_pepper="pepper",
        bot_service_secret="secret",
        bot_mode="webhook",
        webhook_base_url="",
    )
    application = MagicMock()
    from bot.main import _run_webhook

    with pytest.raises(SystemExit, match="WEBHOOK_BASE_URL"):
        _run_webhook(application, settings)
