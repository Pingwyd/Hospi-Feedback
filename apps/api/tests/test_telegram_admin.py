"""Tests for Telegram link codes and admin chat-id resolution."""

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from app.core.crypto import encrypt_telegram_chat_id, generate_aes256_key_b64
from app.core.link_code import generate_link_code, hash_link_code
from app.exceptions.telegram_admin import (
    TelegramAdminNotLinkedError,
    TelegramLinkRejectedError,
)
from app.main import create_app
from app.services.telegram_admin import (
    _crypto_environ,
    generate_telegram_link_code,
    link_telegram_account,
    resolve_admin_id_from_telegram_chat_id,
)
from fastapi.testclient import TestClient

FIXTURE_ADMIN_ID = "00000000-0000-0000-0000-000000000101"
FIXTURE_BOT_SECRET = "unit-test-bot-service-secret"
FIXTURE_CHAT_ID = "123456789"
FIXTURE_ENCRYPTION_KEY = generate_aes256_key_b64()


@pytest.fixture
def telegram_env(api_env: None, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BOT_SERVICE_SECRET", FIXTURE_BOT_SECRET)
    monkeypatch.setenv("TELEGRAM_CHAT_ID_ENCRYPTION_KEY", FIXTURE_ENCRYPTION_KEY)
    monkeypatch.setenv("TELEGRAM_LINK_CODE_TTL_SECONDS", "600")
    from app.core.settings import get_settings

    get_settings.cache_clear()


@pytest.fixture
def client(telegram_env: None) -> TestClient:
    return TestClient(create_app())


def test_crypto_environ_uses_settings_when_process_env_missing(
    telegram_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.core.crypto import ENV_KEY_NAME
    from app.core.settings import get_settings

    settings = get_settings()
    monkeypatch.delenv("TELEGRAM_CHAT_ID_ENCRYPTION_KEY", raising=False)
    assert _crypto_environ(settings)[ENV_KEY_NAME] == FIXTURE_ENCRYPTION_KEY


def test_generate_link_code_invalidates_prior_and_returns_plaintext(
    telegram_env: None,
) -> None:
    with (
        patch(
            "app.services.telegram_admin.invalidate_unused_codes_for_admin"
        ) as mock_invalidate,
        patch("app.services.telegram_admin.insert_link_code") as mock_insert,
        patch(
            "app.services.telegram_admin.generate_link_code",
            return_value="ABCD2345EFGH",
        ),
    ):
        from app.core.settings import get_settings

        result = generate_telegram_link_code(
            admin_id=FIXTURE_ADMIN_ID,
            settings=get_settings(),
        )
    assert result.link_code == "ABCD2345EFGH"
    mock_invalidate.assert_called_once()
    mock_insert.assert_called_once()
    assert mock_insert.call_args.kwargs["code_hash"] == hash_link_code("ABCD2345EFGH")


def test_link_telegram_account_encrypts_and_marks_code_used(
    telegram_env: None,
) -> None:
    code = generate_link_code()
    now = datetime.now(tz=UTC)
    row = {
        "id": "00000000-0000-0000-0000-000000000201",
        "admin_id": FIXTURE_ADMIN_ID,
        "expires_at": (now + timedelta(minutes=5)).isoformat().replace("+00:00", "Z"),
    }
    with (
        patch(
            "app.services.telegram_admin.fetch_active_link_code_by_hash",
            return_value=row,
        ),
        patch(
            "app.services.telegram_admin.update_admin_telegram_chat_id"
        ) as mock_update,
        patch("app.services.telegram_admin.mark_link_code_used") as mock_used,
    ):
        from app.core.settings import get_settings

        admin_id = link_telegram_account(
            one_time_code=code,
            telegram_chat_id=FIXTURE_CHAT_ID,
            settings=get_settings(),
        )
    assert admin_id == FIXTURE_ADMIN_ID
    mock_update.assert_called_once()
    encrypted = mock_update.call_args.kwargs["telegram_chat_id_encrypted"]
    assert encrypted
    mock_used.assert_called_once()


def test_link_telegram_account_rejects_expired_code(telegram_env: None) -> None:
    code = generate_link_code()
    row = {
        "id": "expired-id",
        "admin_id": FIXTURE_ADMIN_ID,
        "expires_at": (datetime.now(tz=UTC) - timedelta(minutes=1))
        .isoformat()
        .replace("+00:00", "Z"),
    }
    with patch(
        "app.services.telegram_admin.fetch_active_link_code_by_hash",
        return_value=row,
    ):
        from app.core.settings import get_settings

        with pytest.raises(TelegramLinkRejectedError):
            link_telegram_account(
                one_time_code=code,
                telegram_chat_id=FIXTURE_CHAT_ID,
                settings=get_settings(),
            )


def test_resolve_admin_id_from_telegram_chat_id(telegram_env: None) -> None:
    encrypted = encrypt_telegram_chat_id(FIXTURE_CHAT_ID)
    with patch(
        "app.services.telegram_admin.fetch_linked_admin_rows",
        return_value=[
            {
                "id": FIXTURE_ADMIN_ID,
                "telegram_chat_id_encrypted": encrypted,
            }
        ],
    ):
        from app.core.settings import get_settings

        admin_id = resolve_admin_id_from_telegram_chat_id(
            telegram_chat_id=FIXTURE_CHAT_ID,
            settings=get_settings(),
        )
    assert admin_id == FIXTURE_ADMIN_ID


def test_resolve_admin_id_raises_when_unlinked(telegram_env: None) -> None:
    with patch(
        "app.services.telegram_admin.fetch_linked_admin_rows",
        return_value=[],
    ):
        from app.core.settings import get_settings

        with pytest.raises(TelegramAdminNotLinkedError):
            resolve_admin_id_from_telegram_chat_id(
                telegram_chat_id=FIXTURE_CHAT_ID,
                settings=get_settings(),
            )


def test_bot_link_endpoint_requires_secret(client: TestClient) -> None:
    response = client.post(
        "/api/admin/telegram/link",
        json={
            "one_time_code": generate_link_code(),
            "telegram_chat_id": FIXTURE_CHAT_ID,
        },
    )
    assert response.status_code == 401


def test_bot_link_endpoint_accepts_valid_secret(client: TestClient) -> None:
    code = generate_link_code()
    row = {
        "id": "00000000-0000-0000-0000-000000000301",
        "admin_id": FIXTURE_ADMIN_ID,
        "expires_at": (datetime.now(tz=UTC) + timedelta(minutes=5))
        .isoformat()
        .replace("+00:00", "Z"),
    }
    with (
        patch(
            "app.services.telegram_admin.fetch_active_link_code_by_hash",
            return_value=row,
        ),
        patch("app.services.telegram_admin.update_admin_telegram_chat_id"),
        patch("app.services.telegram_admin.mark_link_code_used"),
    ):
        response = client.post(
            "/api/admin/telegram/link",
            json={
                "one_time_code": code,
                "telegram_chat_id": FIXTURE_CHAT_ID,
            },
            headers={"X-Bot-Service-Secret": FIXTURE_BOT_SECRET},
        )
    assert response.status_code == 200
    assert response.json() == {"linked": True}


def test_generate_link_code_requires_admin_session(client: TestClient) -> None:
    response = client.post("/api/admin/telegram/link-code")
    assert response.status_code == 401


def test_generate_link_code_returns_plaintext_once(client: TestClient) -> None:
    from app.api.deps import require_admin
    from app.core.admin_auth import AdminContext

    app = create_app()
    app.dependency_overrides[require_admin] = lambda: AdminContext(
        id=FIXTURE_ADMIN_ID,
        full_name="Test Admin",
        role="hoh",
        subunit=None,
        aliases=(),
        permissions=frozenset({"view"}),
    )
    authed_client = TestClient(app)
    with patch(
        "app.api.routes.admin_telegram.generate_telegram_link_code",
        return_value=type(
            "Result",
            (),
            {
                "link_code": "ABCD2345EFGH",
                "expires_at": datetime(2026, 9, 8, 12, 0, tzinfo=UTC),
            },
        )(),
    ):
        response = authed_client.post("/api/admin/telegram/link-code")
    assert response.status_code == 200
    assert response.json()["link_code"] == "ABCD2345EFGH"
