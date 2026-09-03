"""FastAPI dependencies shared by later phases. Do not copy these per route."""

from collections.abc import Callable
from typing import Annotated, Any

from fastapi import Cookie, Depends, Header

from app.core.access_session import verify_access_token
from app.core.admin_auth import (
    AdminContext,
    load_admin_context,
    verify_supabase_access_token,
)
from app.core.settings import Settings, get_settings
from app.exceptions.access import AccessDeniedError
from app.exceptions.auth import AdminSessionError, PermissionDeniedError


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
    claims = verify_supabase_access_token(token, secret=settings.supabase_jwt_secret)
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
