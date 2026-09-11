"""Admin categories and escalation contact routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr, Field

from app.api.deps import require_permission
from app.core.admin_auth import AdminContext
from app.core.settings import Settings, get_settings
from app.services.admin_config import (
    create_category,
    create_escalation_contact,
    list_admin_categories,
    list_admin_escalation_contacts,
    update_category,
    update_escalation_contact,
)

router = APIRouter(tags=["admin-config"])


class CategoryCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class CategoryPatchRequest(BaseModel):
    name: str | None = None
    active: bool | None = None


class EscalationContactCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    role_label: str = Field(min_length=1, max_length=200)
    contact_email: EmailStr | None = None
    contact_phone: str | None = None


class EscalationContactPatchRequest(BaseModel):
    name: str | None = None
    role_label: str | None = None
    contact_email: EmailStr | None = None
    contact_phone: str | None = None
    active: bool | None = None


@router.get("/api/admin/categories")
def get_categories(
    admin: AdminContext = Depends(require_permission("view")),
    settings: Settings = Depends(get_settings),
) -> dict[str, list[dict[str, Any]]]:
    return {"data": list_admin_categories(admin=admin, settings=settings)}


@router.post("/api/admin/categories", status_code=201)
def post_category(
    body: CategoryCreateRequest,
    admin: AdminContext = Depends(require_permission("manage_categories")),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    row = create_category(name=body.name, admin=admin, settings=settings)
    return {"data": row}


@router.patch("/api/admin/categories/{category_id}")
def patch_category_route(
    category_id: str,
    body: CategoryPatchRequest,
    admin: AdminContext = Depends(require_permission("manage_categories")),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    fields = body.model_dump(exclude_none=True)
    row = update_category(
        category_id=category_id,
        fields=fields,
        admin=admin,
        settings=settings,
    )
    return {"data": row}


@router.get("/api/admin/escalation-contacts")
def get_escalation_contacts(
    admin: AdminContext = Depends(require_permission("view")),
    settings: Settings = Depends(get_settings),
) -> dict[str, list[dict[str, Any]]]:
    return {"data": list_admin_escalation_contacts(admin=admin, settings=settings)}


@router.post("/api/admin/escalation-contacts", status_code=201)
def post_escalation_contact(
    body: EscalationContactCreateRequest,
    admin: AdminContext = Depends(require_permission("manage_escalation_contacts")),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    row = create_escalation_contact(
        row=body.model_dump(exclude_none=True),
        admin=admin,
        settings=settings,
    )
    return {"data": row}


@router.patch("/api/admin/escalation-contacts/{contact_id}")
def patch_escalation_contact_route(
    contact_id: str,
    body: EscalationContactPatchRequest,
    admin: AdminContext = Depends(require_permission("manage_escalation_contacts")),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    fields = body.model_dump(exclude_none=True)
    row = update_escalation_contact(
        contact_id=contact_id,
        fields=fields,
        admin=admin,
        settings=settings,
    )
    return {"data": row}
