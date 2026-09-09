"""FastAPI dependencies shared by later phases. Do not copy these per route."""

import hmac
from collections.abc import Callable
from typing import Annotated, Any

from fastapi import Cookie, Depends, Header, HTTPException, status

from app.core.access_session import verify_access_token
from app.core.admin_auth import (
    AdminContext,
    load_admin_context,
    verify_supabase_access_token,
)
from app.core.settings import Settings, get_settings
from app.exceptions.access import AccessDeniedError
from app.exceptions.admin_reports import HohRoleRequiredError
from app.exceptions.auth import AdminSessionError, PermissionDeniedError
from app.services.telegram_admin import resolve_admin_id_from_telegram_chat_id


def _bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, _, value = authorization.partition(" ")
    if scheme.lower() != "bearer" or not value:
        return None
    return value.strip() or None


def require_access_session(
    settings: Annotated[Settings, Depends(get_settings)],
    authorization: Annotated[str | None, Header()] = None,
    hospi_access_session: Annotated[str | None, Cookie()] = None,
) -> dict[str, Any]:
    """Reject requests without a valid access-code session JWT.

    Web sends the httpOnly cookie. The bot sends Authorization Bearer.
    """
    token = _bearer_token(authorization) or hospi_access_session
    if not token:
        raise AccessDeniedError("Access session required.")
    return verify_access_token(token, secret=settings.access_code_jwt_secret)


def require_admin(
    settings: Annotated[Settings, Depends(get_settings)],
    authorization: Annotated[str | None, Header()] = None,
) -> AdminContext:
    """Resolve the authenticated admin and their permission rows."""
    token = _bearer_token(authorization)
    if not token:
        raise AdminSessionError("Admin session required.")
    claims = verify_supabase_access_token(token, settings=settings)
    return load_admin_context(str(claims["sub"]), settings=settings)


def require_permission(permission: str) -> Callable[..., AdminContext]:
    """FastAPI dependency factory for a single admin_permissions row."""

    def _require_permission(
        admin: Annotated[AdminContext, Depends(require_admin)],
    ) -> AdminContext:
        if permission not in admin.permissions:
            raise PermissionDeniedError(
                f"Permission '{permission}' is required for this action.",
            )
        return admin

    return _require_permission


def require_hoh(
    admin: Annotated[AdminContext, Depends(require_admin)],
) -> AdminContext:
    """Restrict an endpoint to the Head of Hospi role."""
    if admin.role != "hoh":
        raise HohRoleRequiredError("Only the Head of Hospi may perform this action.")
    return admin


def require_roles(*allowed_roles: str) -> Callable[..., AdminContext]:
    """Restrict an endpoint to admins whose role is in allowed_roles."""
    allowed = frozenset(allowed_roles)

    def _require_roles(
        admin: Annotated[AdminContext, Depends(require_admin)],
    ) -> AdminContext:
        if admin.role not in allowed:
            raise PermissionDeniedError(
                f"Role must be one of {sorted(allowed)} for this action.",
            )
        return admin

    return _require_roles


def require_bot_service_secret(
    settings: Annotated[Settings, Depends(get_settings)],
    x_bot_service_secret: Annotated[str | None, Header()] = None,
) -> None:
    """Reject bot-only endpoints when the shared bot secret is missing or wrong."""
    expected = settings.bot_service_secret.strip()
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Bot service secret is not configured.",
        )
    provided = (x_bot_service_secret or "").strip()
    if not provided or not hmac.compare_digest(provided, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bot service secret.",
        )


def require_bot_admin(
    telegram_chat_id: str,
    settings: Annotated[Settings, Depends(get_settings)],
    _bot_secret: Annotated[None, Depends(require_bot_service_secret)],
) -> AdminContext:
    """Resolve admin_id from plaintext Telegram chat_id (bot-only routes)."""
    admin_id = resolve_admin_id_from_telegram_chat_id(
        telegram_chat_id=telegram_chat_id,
        settings=settings,
    )
    return load_admin_context(admin_id, settings=settings)
