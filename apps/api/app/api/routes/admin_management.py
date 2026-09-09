"""Admin user management routes."""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr, Field

from app.api.deps import require_permission
from app.core.admin_auth import AdminContext
from app.core.settings import Settings, get_settings
from app.services.admin_management import (
    create_admin_user,
    deactivate_admin_user,
    list_admin_users,
    update_admin_permissions,
)

router = APIRouter(tags=["admin-management"])

AdminRole = Literal[
    "hoh",
    "asst_head",
    "gen_sec",
    "fin_sec",
    "subunit_head",
    "subunit_asst",
    "custom",
]


class CreateAdminRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12)
    full_name: str = Field(min_length=1, max_length=200)
    role: AdminRole
    subunit: str | None = None
    permissions: list[str] = Field(default_factory=list)


class UpdatePermissionsRequest(BaseModel):
    permissions: list[str]


@router.get("/api/admin/admins")
def get_admins(
    admin: AdminContext = Depends(require_permission("manage_admins")),
    settings: Settings = Depends(get_settings),
) -> dict[str, list[dict[str, Any]]]:
    return {"data": list_admin_users(admin=admin, settings=settings)}


@router.post("/api/admin/admins", status_code=201)
def post_admin(
    body: CreateAdminRequest,
    admin: AdminContext = Depends(require_permission("manage_admins")),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    row = create_admin_user(
        email=str(body.email),
        password=body.password,
        full_name=body.full_name,
        role=body.role,
        subunit=body.subunit,
        permissions=body.permissions,
        admin=admin,
        settings=settings,
    )
    return {"data": row}


@router.patch("/api/admin/admins/{admin_id}/permissions")
def patch_admin_permissions_route(
    admin_id: str,
    body: UpdatePermissionsRequest,
    admin: AdminContext = Depends(require_permission("manage_admins")),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    row = update_admin_permissions(
        target_admin_id=admin_id,
        permissions=body.permissions,
        admin=admin,
        settings=settings,
    )
    return {"data": row}


@router.patch("/api/admin/admins/{admin_id}/deactivate")
def patch_admin_deactivate_route(
    admin_id: str,
    admin: AdminContext = Depends(require_permission("manage_admins")),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    row = deactivate_admin_user(
        target_admin_id=admin_id,
        admin=admin,
        settings=settings,
    )
    return {"data": row}
