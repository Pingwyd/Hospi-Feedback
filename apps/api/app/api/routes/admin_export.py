"""Admin filtered on-demand report export."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response

from app.api.deps import require_permission
from app.core.admin_auth import AdminContext
from app.core.settings import Settings, get_settings
from app.services.admin_export import ExportFormat, build_filtered_admin_export

router = APIRouter(tags=["admin-export"])


@router.get("/api/admin/export")
def export_filtered_reports_route(
    admin: AdminContext = Depends(require_permission("export")),
    settings: Settings = Depends(get_settings),
    export_format: ExportFormat = Query(default="pdf", alias="format"),
    status: str | None = Query(default=None),
    keyword: str | None = Query(default=None),
    created_from: str | None = Query(default=None),
    created_to: str | None = Query(default=None),
) -> Response:
    content, filename, media_type = build_filtered_admin_export(
        admin=admin,
        settings=settings,
        export_format=export_format,
        status=status,
        keyword=keyword,
        created_from=created_from,
        created_to=created_to,
    )
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
