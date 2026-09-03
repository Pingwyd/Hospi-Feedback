"""Phase 2 placeholders used only to prove shared dependencies. Not product routes."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends

from app.api.deps import require_access_session, require_admin, require_permission
from app.core.admin_auth import AdminContext

router = APIRouter(tags=["phase2-placeholders"])


@router.get("/api/_phase2/public-ping")
def public_ping(
    _session: Annotated[dict[str, Any], Depends(require_access_session)],
) -> dict[str, bool]:
    return {"ok": True}


@router.get("/api/_phase2/admin-ping")
def admin_ping(
    admin: Annotated[AdminContext, Depends(require_admin)],
) -> dict[str, bool | str]:
    return {"ok": True, "admin_id": admin.id}


@router.get("/api/_phase2/admin-export-ping")
def admin_export_ping(
    admin: Annotated[AdminContext, Depends(require_permission("export"))],
) -> dict[str, bool | str]:
    return {"ok": True, "admin_id": admin.id}
