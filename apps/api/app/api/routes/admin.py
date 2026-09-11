from datetime import UTC

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.deps import require_admin, require_permission
from app.core.admin_auth import AdminContext
from app.core.admin_login import AdminLoginResult, admin_login
from app.core.settings import Settings, get_settings
from app.integrations.admin_management_store import list_admins

router = APIRouter(tags=["admin"])


class AdminLoginRequest(BaseModel):
    email: str = Field(min_length=3)
    password: str = Field(min_length=1)
    totp_code: str | None = None


class AdminLoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_at: str


class AdminProfileResponse(BaseModel):
    id: str
    full_name: str
    role: str | None
    subunit: str | None
    permissions: list[str]


class AdminTeamMember(BaseModel):
    id: str
    full_name: str
    role: str | None


@router.get("/api/admin/me")
def get_current_admin(
    admin: AdminContext = Depends(require_admin),
) -> dict[str, AdminProfileResponse]:
    return {
        "data": AdminProfileResponse(
            id=admin.id,
            full_name=admin.full_name,
            role=admin.role,
            subunit=admin.subunit,
            permissions=sorted(admin.permissions),
        )
    }


@router.get("/api/admin/team")
def get_admin_team(
    admin: AdminContext = Depends(require_permission("view")),
    settings: Settings = Depends(get_settings),
) -> dict[str, list[AdminTeamMember]]:
    _ = admin
    rows = list_admins(
        supabase_url=settings.supabase_url,
        service_role_key=settings.supabase_service_role_key,
    )
    team = [
        AdminTeamMember(
            id=str(row["id"]),
            full_name=str(row.get("full_name") or "Unknown"),
            role=row.get("role"),
        )
        for row in rows
        if row.get("active", True)
    ]
    return {"data": team}


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
