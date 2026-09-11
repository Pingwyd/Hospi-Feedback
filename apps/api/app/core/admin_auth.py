"""Verify Supabase admin JWTs and load admin rows from Postgres via PostgREST."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import jwt
from jwt import PyJWKClient

from app.core.settings import Settings
from app.exceptions.auth import AdminSessionError
from app.integrations.supabase_rest import (
    AdminRecord,
    fetch_active_admin,
    fetch_admin_permissions,
)

SUPABASE_JWT_ALG_HS256 = "HS256"
SUPABASE_JWT_ALG_ES256 = "ES256"
SUPABASE_JWT_ALG = SUPABASE_JWT_ALG_HS256
SUPABASE_JWT_AUD = "authenticated"
SUPABASE_JWT_ROLE = "authenticated"


@dataclass(frozen=True)
class AdminContext:
    id: str
    full_name: str
    role: str | None
    subunit: str | None
    aliases: tuple[str, ...]
    permissions: frozenset[str]


@lru_cache
def _jwks_client(supabase_url: str) -> PyJWKClient:
    jwks_url = f"{supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
    return PyJWKClient(jwks_url, cache_keys=True)


def _decode_supabase_jwt(token: str, *, settings: Settings) -> dict[str, Any]:
    header = jwt.get_unverified_header(token)
    algorithm = header.get("alg")
    decode_options = {"require": ["exp", "sub", "role"]}

    if algorithm == SUPABASE_JWT_ALG_ES256:
        client = _jwks_client(settings.supabase_url)
        signing_key = client.get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=[SUPABASE_JWT_ALG_ES256],
            audience=SUPABASE_JWT_AUD,
            options=decode_options,
        )

    return jwt.decode(
        token,
        settings.supabase_jwt_secret,
        algorithms=[SUPABASE_JWT_ALG_HS256],
        audience=SUPABASE_JWT_AUD,
        options=decode_options,
    )


def verify_supabase_access_token(token: str, *, settings: Settings) -> dict[str, Any]:
    if not token:
        raise AdminSessionError("Admin session required.")
    try:
        claims = _decode_supabase_jwt(token, settings=settings)
    except jwt.ExpiredSignatureError as exc:
        raise AdminSessionError("Admin session expired.") from exc
    except jwt.InvalidTokenError as exc:
        raise AdminSessionError("Admin session invalid.") from exc
    if claims.get("role") != SUPABASE_JWT_ROLE:
        raise AdminSessionError("Admin session invalid.")
    if not claims.get("sub"):
        raise AdminSessionError("Admin session invalid.")
    return claims


def load_admin_context(admin_id: str, *, settings: Settings) -> AdminContext:
    record = fetch_active_admin(
        supabase_url=settings.supabase_url,
        service_role_key=settings.supabase_service_role_key,
        admin_id=admin_id,
    )
    if record is None:
        raise AdminSessionError("Admin account inactive or not found.")
    permissions = fetch_admin_permissions(
        supabase_url=settings.supabase_url,
        service_role_key=settings.supabase_service_role_key,
        admin_id=admin_id,
    )
    return admin_context_from_record(record, permissions)


def admin_context_from_record(
    record: AdminRecord,
    permissions: frozenset[str],
) -> AdminContext:
    return AdminContext(
        id=record.id,
        full_name=record.full_name,
        role=record.role,
        subunit=record.subunit,
        aliases=record.aliases,
        permissions=permissions,
    )
