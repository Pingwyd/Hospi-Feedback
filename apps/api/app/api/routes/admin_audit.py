"""Audit log viewer routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query

from app.api.deps import require_roles
from app.core.admin_auth import AdminContext
from app.core.settings import Settings, get_settings
from app.services.admin_audit import list_audit_log

router = APIRouter(tags=["admin-audit"])


@router.get("/api/admin/audit-log")
def get_audit_log(
    admin: AdminContext = Depends(require_roles("hoh", "asst_head")),
    settings: Settings = Depends(get_settings),
    report_id: str | None = Query(default=None),
    admin_id: str | None = Query(default=None),
    action: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> dict[str, list[dict[str, Any]]]:
    rows = list_audit_log(
        admin=admin,
        settings=settings,
        report_id=report_id,
        actor_admin_id=admin_id,
        action=action,
        limit=limit,
        offset=offset,
    )
    return {"data": rows}
