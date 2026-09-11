"""Audit log read service for HOH and Assistant Heads."""

from __future__ import annotations

from app.core.admin_auth import AdminContext
from app.core.settings import Settings
from app.integrations.audit_log_store import list_audit_log_entries


def _store_kwargs(settings: Settings) -> dict[str, str]:
    return {
        "supabase_url": settings.supabase_url,
        "service_role_key": settings.supabase_service_role_key,
    }


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
    return list_audit_log_entries(
        **_store_kwargs(settings),
        report_id=report_id,
        admin_id=actor_admin_id,
        action=action,
        limit=limit,
        offset=offset,
    )
