"""Audit log read service for HOH and Assistant Heads."""

from __future__ import annotations

from typing import Any

from app.core.admin_auth import AdminContext
from app.core.settings import Settings
from app.integrations.admin_management_store import fetch_admins_by_ids
from app.integrations.audit_log_store import list_audit_log_entries

FORMER_ADMIN_LABEL = "Former admin (removed)"
UNKNOWN_ADMIN_LABEL = "Unknown admin"


def _store_kwargs(settings: Settings) -> dict[str, str]:
    return {
        "supabase_url": settings.supabase_url,
        "service_role_key": settings.supabase_service_role_key,
    }


def _attach_admin_display_fields(
    rows: list[dict[str, Any]],
    *,
    settings: Settings,
) -> list[dict[str, Any]]:
    admin_ids = [
        str(row["admin_id"])
        for row in rows
        if row.get("admin_id") is not None and str(row.get("admin_id")).strip()
    ]
    admin_rows = fetch_admins_by_ids(
        **_store_kwargs(settings),
        admin_ids=admin_ids,
    )
    enriched: list[dict[str, Any]] = []
    for row in rows:
        copy = dict(row)
        admin_id = copy.get("admin_id")
        if admin_id is None or not str(admin_id).strip():
            copy["admin_display_name"] = FORMER_ADMIN_LABEL
            copy["admin_role"] = None
        else:
            admin_key = str(admin_id)
            admin_record = admin_rows.get(admin_key)
            if admin_record is None:
                copy["admin_display_name"] = UNKNOWN_ADMIN_LABEL
                copy["admin_role"] = None
            else:
                copy["admin_display_name"] = str(admin_record.get("full_name") or "").strip()
                if not copy["admin_display_name"]:
                    copy["admin_display_name"] = UNKNOWN_ADMIN_LABEL
                role = admin_record.get("role")
                copy["admin_role"] = str(role) if role else None
        enriched.append(copy)
    return enriched


def list_audit_log(
    *,
    admin: AdminContext,
    settings: Settings,
    report_id: str | None = None,
    actor_admin_id: str | None = None,
    action: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    _ = admin
    rows = list_audit_log_entries(
        **_store_kwargs(settings),
        report_id=report_id,
        admin_id=actor_admin_id,
        action=action,
        limit=limit,
        offset=offset,
    )
    return _attach_admin_display_fields(rows, settings=settings)
