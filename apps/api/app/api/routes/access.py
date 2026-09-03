from datetime import UTC

from fastapi import APIRouter, Depends, Header, Response
from pydantic import BaseModel, Field

from app.core.access_session import access_code_matches, issue_access_token
from app.core.settings import Settings, get_settings
from app.exceptions.access import AccessCodeRejectedError

router = APIRouter(tags=["access"])

BEARER_TRANSPORT = "bearer"


class AccessVerifyRequest(BaseModel):
    access_code: str = Field(min_length=1)


class AccessVerifyResponse(BaseModel):
    expires_at: str
    session_token: str | None = None


@router.post("/api/access/verify", response_model=AccessVerifyResponse)
def verify_access_code(
    body: AccessVerifyRequest,
    response: Response,
    settings: Settings = Depends(get_settings),
    x_session_transport: str | None = Header(default=None),
) -> AccessVerifyResponse:
    if not access_code_matches(body.access_code, settings.shared_access_code):
        raise AccessCodeRejectedError("Invalid access code.")

    token, expires_at = issue_access_token(
        secret=settings.access_code_jwt_secret,
        ttl_seconds=settings.access_session_ttl_seconds,
    )
    response.set_cookie(
        key=settings.access_cookie_name,
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
        max_age=settings.access_session_ttl_seconds,
    )
    include_token = (x_session_transport or "").strip().lower() == BEARER_TRANSPORT
    return AccessVerifyResponse(
        expires_at=expires_at.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        session_token=token if include_token else None,
    )
