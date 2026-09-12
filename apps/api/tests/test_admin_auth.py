from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import jwt
import pytest
from app.core.admin_auth import SUPABASE_JWT_ALG, SUPABASE_JWT_AUD
from app.core.admin_login import AdminLoginResult
from app.core.settings import get_settings
from app.integrations.gotrue_auth import GoTrueSession
from app.integrations.supabase_rest import AdminRecord
from app.main import create_app
from fastapi.testclient import TestClient
from tests.conftest import FIXTURE_SUPABASE_JWT_SECRET

ADMIN_ID = "11111111-1111-1111-1111-111111111111"
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "local-only-password-fixture"
TOTP_CODE = "123456"
FACTOR_ID = "22222222-2222-2222-2222-222222222222"


@pytest.fixture
def client(api_env: None) -> TestClient:
    return TestClient(create_app())


def _password_session() -> GoTrueSession:
    return GoTrueSession(
        access_token="aal1-access-token",
        refresh_token="aal1-refresh-token",
        expires_in=3600,
        user_id=ADMIN_ID,
    )


def _aal2_session() -> GoTrueSession:
    return GoTrueSession(
        access_token="aal2-access-token",
        refresh_token="aal2-refresh-token",
        expires_in=3600,
        user_id=ADMIN_ID,
    )


def _admin_record() -> AdminRecord:
    return AdminRecord(
        id=ADMIN_ID,
        full_name="Local Bootstrap HOH",
        role="hoh",
        subunit=None,
        aliases=("HOH",),
        active=True,
    )


def _issue_admin_token(*, permissions: frozenset[str] | None = None) -> str:
    now = datetime.now(tz=UTC)
    payload = {
        "sub": ADMIN_ID,
        "role": "authenticated",
        "aud": SUPABASE_JWT_AUD,
        "iat": now,
        "exp": now + timedelta(hours=1),
    }
    return jwt.encode(payload, FIXTURE_SUPABASE_JWT_SECRET, algorithm=SUPABASE_JWT_ALG)


@patch("app.api.routes.admin.admin_login")
def test_login_rejects_when_2fa_not_configured(
    admin_login_mock: MagicMock,
    client: TestClient,
) -> None:
    from app.exceptions.auth import AdminLoginRejectedError

    admin_login_mock.side_effect = AdminLoginRejectedError(
        "Two-factor authentication is not configured for this account. "
        "Set up an authenticator app before signing in.",
    )
    response = client.post(
        "/api/admin/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    assert response.status_code == 401
    assert (
        "Two-factor authentication is not configured"
        in response.json()["error"]["message"]
    )


@patch("app.api.routes.admin.admin_login")
def test_login_rejects_missing_totp_code(
    admin_login_mock: MagicMock,
    client: TestClient,
) -> None:
    from app.exceptions.auth import AdminLoginRejectedError

    admin_login_mock.side_effect = AdminLoginRejectedError(
        "Second factor required. Provide a TOTP code from your authenticator app.",
    )
    response = client.post(
        "/api/admin/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    assert response.status_code == 401
    assert "Second factor required" in response.json()["error"]["message"]


@patch("app.api.routes.admin.admin_login")
def test_login_with_totp_returns_session(
    admin_login_mock: MagicMock,
    client: TestClient,
) -> None:
    expires_at = datetime.now(tz=UTC) + timedelta(hours=1)
    admin_login_mock.return_value = AdminLoginResult(
        access_token="aal2-access-token",
        refresh_token="aal2-refresh-token",
        expires_at=expires_at,
        user_id=ADMIN_ID,
    )
    response = client.post(
        "/api/admin/login",
        json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD,
            "totp_code": TOTP_CODE,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["access_token"] == "aal2-access-token"
    assert body["refresh_token"] == "aal2-refresh-token"
    assert body["expires_at"].endswith("Z")


@patch("app.core.admin_login.verify_mfa_challenge")
@patch("app.core.admin_login.create_mfa_challenge")
@patch("app.core.admin_login.list_user_mfa_factors")
@patch("app.core.admin_login.sign_in_with_password")
def test_admin_login_orchestration_requires_verified_totp(
    sign_in_mock: MagicMock,
    list_factors_mock: MagicMock,
    challenge_mock: MagicMock,
    verify_mock: MagicMock,
    api_env: None,
) -> None:
    from app.core.admin_login import admin_login
    from app.exceptions.auth import AdminLoginRejectedError

    sign_in_mock.return_value = _password_session()
    list_factors_mock.return_value = []
    settings = get_settings()
    with pytest.raises(
        AdminLoginRejectedError, match="Two-factor authentication is not configured"
    ):
        admin_login(
            email=ADMIN_EMAIL,
            password=ADMIN_PASSWORD,
            totp_code=TOTP_CODE,
            settings=settings,
        )
    challenge_mock.assert_not_called()
    verify_mock.assert_not_called()


@patch("app.core.admin_login.verify_mfa_challenge")
@patch("app.core.admin_login.create_mfa_challenge")
@patch("app.core.admin_login.list_user_mfa_factors")
@patch("app.core.admin_login.sign_in_with_password")
def test_admin_login_orchestration_success(
    sign_in_mock: MagicMock,
    list_factors_mock: MagicMock,
    challenge_mock: MagicMock,
    verify_mock: MagicMock,
    api_env: None,
) -> None:
    from app.core.admin_login import admin_login

    sign_in_mock.return_value = _password_session()
    list_factors_mock.return_value = [
        {
            "id": FACTOR_ID,
            "factor_type": "totp",
            "status": "verified",
        }
    ]
    challenge_mock.return_value = "challenge-id-fixture"
    verify_mock.return_value = _aal2_session()
    settings = get_settings()
    result = admin_login(
        email=ADMIN_EMAIL,
        password=ADMIN_PASSWORD,
        totp_code=TOTP_CODE,
        settings=settings,
    )
    assert result.access_token == "aal2-access-token"
    verify_mock.assert_called_once()


@patch("app.core.admin_login.sign_in_with_password")
def test_admin_login_skips_2fa_when_disabled(
    sign_in_mock: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
    api_env: None,
) -> None:
    from app.core.admin_login import admin_login

    monkeypatch.setenv("ADMIN_2FA_REQUIRED", "false")
    get_settings.cache_clear()
    sign_in_mock.return_value = _password_session()
    settings = get_settings()
    result = admin_login(
        email=ADMIN_EMAIL,
        password=ADMIN_PASSWORD,
        totp_code=None,
        settings=settings,
    )
    assert result.access_token == "aal1-access-token"
    sign_in_mock.assert_called_once()


@patch("app.core.admin_auth.fetch_admin_permissions")
@patch("app.core.admin_auth.fetch_active_admin")
def test_admin_ping_accepts_valid_session(
    fetch_admin_mock: MagicMock,
    fetch_permissions_mock: MagicMock,
    client: TestClient,
) -> None:
    fetch_admin_mock.return_value = _admin_record()
    fetch_permissions_mock.return_value = frozenset({"view"})
    token = _issue_admin_token()
    response = client.get(
        "/api/_phase2/admin-ping",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json() == {"ok": True, "admin_id": ADMIN_ID}


def test_verify_supabase_token_rejects_non_authenticated_role(api_env: None) -> None:
    from app.core.admin_auth import verify_supabase_access_token
    from app.exceptions.auth import AdminSessionError

    now = datetime.now(tz=UTC)
    token = jwt.encode(
        {
            "sub": ADMIN_ID,
            "role": "anon",
            "aud": SUPABASE_JWT_AUD,
            "iat": now,
            "exp": now + timedelta(hours=1),
        },
        FIXTURE_SUPABASE_JWT_SECRET,
        algorithm=SUPABASE_JWT_ALG,
    )
    with pytest.raises(AdminSessionError, match="Admin session invalid"):
        verify_supabase_access_token(token, settings=get_settings())
