"""Admin login orchestration: password, MFA factor checks, and TOTP verification."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.core.settings import Settings
from app.exceptions.auth import AdminLoginRejectedError
from app.exceptions.gotrue import GoTrueAdminError
from app.integrations.gotrue_auth import (
    create_mfa_challenge,
    list_user_mfa_factors,
    sign_in_with_password,
    verify_mfa_challenge,
)

TOTP_FACTOR_TYPE = "totp"
VERIFIED_FACTOR_STATUS = "verified"


@dataclass(frozen=True)
class AdminLoginResult:
    access_token: str
    refresh_token: str
    expires_at: datetime
    user_id: str


def _verified_totp_factors(factors: list[dict]) -> list[dict]:
    return [
        factor
        for factor in factors
        if factor.get("factor_type") == TOTP_FACTOR_TYPE
        and factor.get("status") == VERIFIED_FACTOR_STATUS
        and factor.get("id")
    ]


def admin_login(
    *,
    email: str,
    password: str,
    totp_code: str | None,
    settings: Settings,
) -> AdminLoginResult:
    try:
        password_session = sign_in_with_password(
            supabase_url=settings.supabase_url,
            anon_key=settings.supabase_anon_key,
            email=email,
            password=password,
        )
    except GoTrueAdminError as exc:
        raise AdminLoginRejectedError(
            "Invalid email or password.",
        ) from exc

    if not settings.admin_2fa_enforced:
        expires_at = datetime.now(tz=UTC) + timedelta(
            seconds=password_session.expires_in
        )
        return AdminLoginResult(
            access_token=password_session.access_token,
            refresh_token=password_session.refresh_token,
            expires_at=expires_at,
            user_id=password_session.user_id,
        )

    factors = list_user_mfa_factors(
        supabase_url=settings.supabase_url,
        service_role_key=settings.supabase_service_role_key,
        user_id=password_session.user_id,
    )
    verified_totp = _verified_totp_factors(factors)
    if not verified_totp:
        raise AdminLoginRejectedError(
            "Two-factor authentication is not configured for this account. "
            "Set up an authenticator app before signing in.",
        )

    if not totp_code or not totp_code.strip():
        raise AdminLoginRejectedError(
            "Second factor required. Provide a TOTP code from your authenticator app.",
        )

    factor_id = str(verified_totp[0]["id"])
    try:
        challenge_id = create_mfa_challenge(
            supabase_url=settings.supabase_url,
            anon_key=settings.supabase_anon_key,
            factor_id=factor_id,
            access_token=password_session.access_token,
        )
        session = verify_mfa_challenge(
            supabase_url=settings.supabase_url,
            anon_key=settings.supabase_anon_key,
            factor_id=factor_id,
            access_token=password_session.access_token,
            challenge_id=challenge_id,
            code=totp_code.strip(),
        )
    except GoTrueAdminError as exc:
        raise AdminLoginRejectedError(
            "Invalid authenticator code.",
        ) from exc

    expires_at = datetime.now(tz=UTC) + timedelta(seconds=session.expires_in)
    return AdminLoginResult(
        access_token=session.access_token,
        refresh_token=session.refresh_token,
        expires_at=expires_at,
        user_id=session.user_id,
    )
