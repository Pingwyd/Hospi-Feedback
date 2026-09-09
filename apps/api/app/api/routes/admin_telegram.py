from datetime import UTC

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.deps import require_admin, require_bot_service_secret
from app.core.admin_auth import AdminContext
from app.core.settings import Settings, get_settings
from app.services.telegram_admin import (
    generate_telegram_link_code,
    link_telegram_account,
)

router = APIRouter(tags=["admin-telegram"])


class GenerateLinkCodeResponse(BaseModel):
    link_code: str
    expires_at: str


class LinkTelegramRequest(BaseModel):
    one_time_code: str = Field(min_length=12, max_length=12)
    telegram_chat_id: str = Field(pattern=r"^-?\d+$")


class LinkTelegramResponse(BaseModel):
    linked: bool


@router.post(
    "/api/admin/telegram/link-code",
    response_model=GenerateLinkCodeResponse,
)
def create_telegram_link_code(
    admin: AdminContext = Depends(require_admin),
    settings: Settings = Depends(get_settings),
) -> GenerateLinkCodeResponse:
    result = generate_telegram_link_code(admin_id=admin.id, settings=settings)
    return GenerateLinkCodeResponse(
        link_code=result.link_code,
        expires_at=result.expires_at.astimezone(UTC).isoformat().replace("+00:00", "Z"),
    )


@router.post("/api/admin/telegram/link", response_model=LinkTelegramResponse)
def complete_telegram_link(
    body: LinkTelegramRequest,
    _bot_secret: None = Depends(require_bot_service_secret),
    settings: Settings = Depends(get_settings),
) -> LinkTelegramResponse:
    link_telegram_account(
        one_time_code=body.one_time_code,
        telegram_chat_id=body.telegram_chat_id,
        settings=settings,
    )
    return LinkTelegramResponse(linked=True)
