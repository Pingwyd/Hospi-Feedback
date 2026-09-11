"""Admin user management service."""

from __future__ import annotations

from typing import Any

from app.core.admin_auth import AdminContext
from app.core.settings import Settings
from app.exceptions.admin_reports import AdminReportValidationError
from app.exceptions.auth import PermissionDeniedError
from app.integrations.admin_management_store import (
    delete_permissions_for_admin,
    insert_admin_permissions,
    insert_admin_row,
    list_admins,
    patch_admin_row,
)
from app.integrations.gotrue_admin import ensure_confirmed_email_user
from app.services.admin_config import validate_permissions
from app.services.audit_log import write_audit_log


def _store_kwargs(settings: Settings) -> dict[str, str]:
    return {
        "supabase_url": settings.supabase_url,
        "service_role_key": settings.supabase_service_role_key,
    }


def _require_manage_admins(admin: AdminContext) -> None:
    if "manage_admins" not in admin.permissions:
        raise PermissionDeniedError(
            "Permission 'manage_admins' is required for this action.",
        )


def _normalize_admin_row(row: dict[str, Any]) -> dict[str, Any]:
    nested = row.pop("admin_permissions", []) or []
    permissions = sorted(
        {
            str(item["permission"])
            for item in nested
            if isinstance(item, dict) and item.get("permission")
        }
    )
    return {**row, "permissions": permissions}


def list_admin_users(*, admin: AdminContext, settings: Settings) -> list[dict]:
    _require_manage_admins(admin)
    rows = list_admins(**_store_kwargs(settings))
    return [_normalize_admin_row(dict(row)) for row in rows]


def create_admin_user(
    *,
    email: str,
    password: str,
    full_name: str,
    role: str,
    subunit: str | None,
    permissions: list[str],
    admin: AdminContext,
    settings: Settings,
) -> dict:
    _require_manage_admins(admin)
    cleaned_email = email.strip()
    cleaned_name = full_name.strip()
    if not cleaned_email or not password.strip() or not cleaned_name:
        raise AdminReportValidationError("email, password, and full_name are required.")
    validated = validate_permissions(permissions)
    user_id = ensure_confirmed_email_user(
        supabase_url=settings.supabase_url,
        service_role_key=settings.supabase_service_role_key,
        email=cleaned_email,
        password=password,
    )
    row = insert_admin_row(
        **_store_kwargs(settings),
        row={
            "id": user_id,
            "full_name": cleaned_name,
            "role": role,
            "subunit": subunit,
            "active": True,
        },
    )
    insert_admin_permissions(
        **_store_kwargs(settings),
        admin_id=user_id,
        permissions=validated,
    )
    write_audit_log(
        settings=settings,
        admin_id=admin.id,
        report_id=None,
        action="other",
        detail={"event": "admin_created", "target_admin_id": user_id},
    )
    return {**row, "permissions": validated}


def update_admin_permissions(
    *,
    target_admin_id: str,
    permissions: list[str],
    admin: AdminContext,
    settings: Settings,
) -> dict:
    _require_manage_admins(admin)
    validated = validate_permissions(permissions)
    store = _store_kwargs(settings)
    delete_permissions_for_admin(**store, admin_id=target_admin_id)
    insert_admin_permissions(
        **store,
        admin_id=target_admin_id,
        permissions=validated,
    )
    write_audit_log(
        settings=settings,
        admin_id=admin.id,
        report_id=None,
        action="other",
        detail={
            "event": "admin_permissions_updated",
            "target_admin_id": target_admin_id,
            "permissions": validated,
        },
    )
    return {"id": target_admin_id, "permissions": validated}


def deactivate_admin_user(
    *,
    target_admin_id: str,
    admin: AdminContext,
    settings: Settings,
) -> dict:
    _require_manage_admins(admin)
    if target_admin_id == admin.id:
        raise AdminReportValidationError("You cannot deactivate your own account.")
    updated = patch_admin_row(
        **_store_kwargs(settings),
        admin_id=target_admin_id,
        fields={"active": False},
    )
    write_audit_log(
        settings=settings,
        admin_id=admin.id,
        report_id=None,
        action="other",
        detail={"event": "admin_deactivated", "target_admin_id": target_admin_id},
    )
    return updated
