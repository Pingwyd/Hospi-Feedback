from datetime import UTC

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.admin_login import AdminLoginResult, admin_login
from app.core.settings import Settings, get_settings

router = APIRouter(tags=["admin"])


class AdminLoginRequest(BaseModel):
    email: str = Field(min_length=3)
    password: str = Field(min_length=1)
    totp_code: str | None = None


class AdminLoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_at: str


@router.post("/api/admin/login", response_model=AdminLoginResponse)
def login_admin(
    body: AdminLoginRequest,
    settings: Settings = Depends(get_settings),
) -> AdminLoginResponse:
    result: AdminLoginResult = admin_login(
        email=str(body.email),
        password=body.password,
        totp_code=body.totp_code,
        settings=settings,
    )
    return AdminLoginResponse(
        access_token=result.access_token,
        refresh_token=result.refresh_token,
        expires_at=result.expires_at.astimezone(UTC).isoformat().replace("+00:00", "Z"),
    )
