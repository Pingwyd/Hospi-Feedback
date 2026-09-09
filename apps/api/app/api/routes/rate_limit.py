from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.deps import require_access_session
from app.core.settings import Settings, get_settings
from app.services.rate_limit import check_and_record_rate_limit

router = APIRouter(tags=["rate-limit"])


class RateLimitCheckRequest(BaseModel):
    channel: Literal["web", "telegram"]
    identifier_hash: str = Field(
        min_length=64,
        max_length=64,
        pattern=r"^[a-f0-9]{64}$",
    )


class RateLimitCheckResponse(BaseModel):
    allowed: bool


@router.post("/api/rate-limit/check", response_model=RateLimitCheckResponse)
def rate_limit_check(
    body: RateLimitCheckRequest,
    _session: Annotated[dict[str, Any], Depends(require_access_session)],
    settings: Settings = Depends(get_settings),
) -> RateLimitCheckResponse:
    check_and_record_rate_limit(
        channel=body.channel,
        identifier_hash=body.identifier_hash,
        settings=settings,
    )
    return RateLimitCheckResponse(allowed=True)
