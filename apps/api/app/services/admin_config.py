"""Admin-managed categories and escalation contacts."""

from __future__ import annotations

from typing import Any

from app.core.admin_auth import AdminContext
from app.core.admin_permissions import ALL_PERMISSIONS
from app.core.settings import Settings
from app.exceptions.admin_reports import AdminReportValidationError
from app.exceptions.auth import PermissionDeniedError
from app.integrations.categories_store import (
    insert_category,
    list_categories,
    patch_category,
)
from app.integrations.escalation_contacts_store import (
    insert_escalation_contact,
    list_escalation_contacts,
    patch_escalation_contact,
)
from app.services.audit_log import write_audit_log


def _store_kwargs(settings: Settings) -> dict[str, str]:
    return {
        "supabase_url": settings.supabase_url,
        "service_role_key": settings.supabase_service_role_key,
    }


def _require_permission(admin: AdminContext, permission: str) -> None:
    if permission not in admin.permissions:
        raise PermissionDeniedError(
            f"Permission '{permission}' is required for this action.",
        )


def list_admin_categories(*, admin: AdminContext, settings: Settings) -> list[dict]:
    _require_permission(admin, "view")
    return list_categories(**_store_kwargs(settings))


def create_category(*, name: str, admin: AdminContext, settings: Settings) -> dict:
    _require_permission(admin, "manage_categories")
    cleaned = name.strip()
    if not cleaned:
        raise AdminReportValidationError("Category name is required.")
    row = insert_category(**_store_kwargs(settings), name=cleaned)
    write_audit_log(
        settings=settings,
        admin_id=admin.id,
        report_id=None,
        action="other",
        detail={"event": "category_created", "category_id": row["id"]},
    )
    return row


def update_category(
    *,
    category_id: str,
    fields: dict[str, Any],
    admin: AdminContext,
    settings: Settings,
) -> dict:
    _require_permission(admin, "manage_categories")
    row = patch_category(
        **_store_kwargs(settings),
        category_id=category_id,
        fields=fields,
    )
    write_audit_log(
        settings=settings,
        admin_id=admin.id,
        report_id=None,
        action="other",
        detail={"event": "category_updated", "category_id": category_id},
    )
    return row


def list_admin_escalation_contacts(
    *, admin: AdminContext, settings: Settings
) -> list[dict]:
    _require_permission(admin, "view")
    return list_escalation_contacts(**_store_kwargs(settings))


def create_escalation_contact(
    *,
    row: dict[str, Any],
    admin: AdminContext,
    settings: Settings,
) -> dict:
    _require_permission(admin, "manage_escalation_contacts")
    created = insert_escalation_contact(**_store_kwargs(settings), row=row)
    write_audit_log(
        settings=settings,
        admin_id=admin.id,
        report_id=None,
        action="other",
        detail={
            "event": "escalation_contact_created",
            "escalation_contact_id": created["id"],
        },
    )
    return created


def update_escalation_contact(
    *,
    contact_id: str,
    fields: dict[str, Any],
    admin: AdminContext,
    settings: Settings,
) -> dict:
    _require_permission(admin, "manage_escalation_contacts")
    updated = patch_escalation_contact(
        **_store_kwargs(settings),
        contact_id=contact_id,
        fields=fields,
    )
    write_audit_log(
        settings=settings,
        admin_id=admin.id,
        report_id=None,
        action="other",
        detail={
            "event": "escalation_contact_updated",
            "escalation_contact_id": contact_id,
        },
    )
    return updated


def validate_permissions(permissions: list[str]) -> list[str]:
    unknown = [perm for perm in permissions if perm not in ALL_PERMISSIONS]
    if unknown:
        raise AdminReportValidationError(f"Unknown permissions: {unknown}")
    return permissions
