"""Issue and verify anonymous access-code session JWTs.

Payload is iat, exp, sid, and typ only. No PII. Never log the token or the code.
"""

from __future__ import annotations

import hashlib
import hmac
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from app.exceptions.access import AccessDeniedError

ACCESS_TOKEN_TYP = "access_session"
ACCESS_TOKEN_ALG = "HS256"


def access_code_matches(submitted: str, expected: str) -> bool:
    """Constant-time compare of SHA-256 digests so length is not leaked directly."""
    left = hashlib.sha256(submitted.encode("utf-8")).digest()
    right = hashlib.sha256(expected.encode("utf-8")).digest()
    return hmac.compare_digest(left, right)


def issue_access_token(*, secret: str, ttl_seconds: int) -> tuple[str, datetime]:
    now = datetime.now(tz=UTC)
    expires_at = now + timedelta(seconds=ttl_seconds)
    payload = {
        "iat": now,
        "exp": expires_at,
        "sid": str(uuid.uuid4()),
        "typ": ACCESS_TOKEN_TYP,
    }
    token = jwt.encode(payload, secret, algorithm=ACCESS_TOKEN_ALG)
    return token, expires_at


def verify_access_token(token: str, *, secret: str) -> dict[str, Any]:
    if not token:
        raise AccessDeniedError("Access session required.")
    try:
        claims = jwt.decode(
            token,
            secret,
            algorithms=[ACCESS_TOKEN_ALG],
            options={"require": ["iat", "exp", "sid", "typ"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise AccessDeniedError("Access session expired.") from exc
    except jwt.InvalidTokenError as exc:
        raise AccessDeniedError("Access session invalid.") from exc
    if claims.get("typ") != ACCESS_TOKEN_TYP:
        raise AccessDeniedError("Access session invalid.")
    if not claims.get("sid"):
        raise AccessDeniedError("Access session invalid.")
    return claims
