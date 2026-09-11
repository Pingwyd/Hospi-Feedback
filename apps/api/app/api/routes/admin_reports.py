"""Admin report triage routes."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Query, Response, status
from pydantic import BaseModel, Field

from app.api.deps import require_admin, require_hoh
from app.core.admin_auth import AdminContext
from app.core.settings import Settings, get_settings
from app.services.admin_reports import (
    add_internal_note,
    apply_report_status_change,
    assign_report,
    delete_report_by_hoh,
    escalate_report,
    get_admin_report,
    link_report_member,
    list_admin_reports,
    mark_report_false,
    send_reporter_message_and_notify,
)

router = APIRouter(tags=["admin-reports"])

ReportStatus = Literal[
    "new",
    "under_review",
    "assigned",
    "in_progress",
    "resolved",
    "escalated",
    "closed",
    "marked_false",
]


class ReportSummary(BaseModel):
    id: str
    source: str | None = None
    report_type: str | None = None
    reported_member_name: str | None = None
    severity: str | None = None
    status: str | None = None
    assigned_admin_id: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ReportListResponse(BaseModel):
    data: list[ReportSummary]


class UpdateStatusRequest(BaseModel):
    status: ReportStatus
    confirm_recusal_override: bool = False


class AssignReportRequest(BaseModel):
    assigned_admin_id: str


class LinkMemberRequest(BaseModel):
    reported_member_admin_id: str


class NoteRequest(BaseModel):
    content: str = Field(min_length=1, max_length=5000)


class MessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=5000)


class EscalateRequest(BaseModel):
    escalation_contact_id: str


class DeleteReportRequest(BaseModel):
    delete_reason: str = Field(min_length=1, max_length=500)


class MarkFalseRequest(BaseModel):
    confirm_recusal_override: bool = False


@router.get("/api/admin/reports", response_model=ReportListResponse)
def list_reports_route(
    admin: AdminContext = Depends(require_admin),
    settings: Settings = Depends(get_settings),
    status: str | None = Query(default=None),
    keyword: str | None = Query(default=None),
    created_from: str | None = Query(default=None),
    created_to: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> ReportListResponse:
    rows = list_admin_reports(
        admin=admin,
        settings=settings,
        status=status,
        keyword=keyword,
        created_from=created_from,
        created_to=created_to,
        limit=limit,
        offset=offset,
    )
    return ReportListResponse(data=[ReportSummary(**row) for row in rows])


@router.get("/api/admin/reports/{report_id}")
def get_report_route(
    report_id: str,
    admin: AdminContext = Depends(require_admin),
    settings: Settings = Depends(get_settings),
) -> dict:
    return get_admin_report(report_id=report_id, admin=admin, settings=settings)


@router.patch("/api/admin/reports/{report_id}/status")
def patch_report_status_route(
    report_id: str,
    body: UpdateStatusRequest,
    admin: AdminContext = Depends(require_admin),
    settings: Settings = Depends(get_settings),
) -> dict:
    updated = apply_report_status_change(
        report_id=report_id,
        new_status=body.status,
        admin=admin,
        settings=settings,
        confirm_recusal_override=body.confirm_recusal_override,
    )
    return {"data": updated}


@router.patch("/api/admin/reports/{report_id}/assign")
def patch_report_assign_route(
    report_id: str,
    body: AssignReportRequest,
    admin: AdminContext = Depends(require_admin),
    settings: Settings = Depends(get_settings),
) -> dict:
    updated = assign_report(
        report_id=report_id,
        assigned_admin_id=body.assigned_admin_id,
        admin=admin,
        settings=settings,
    )
    return {"data": updated}


@router.patch("/api/admin/reports/{report_id}/link-member")
def patch_report_link_member_route(
    report_id: str,
    body: LinkMemberRequest,
    admin: AdminContext = Depends(require_admin),
    settings: Settings = Depends(get_settings),
) -> dict:
    updated = link_report_member(
        report_id=report_id,
        reported_member_admin_id=body.reported_member_admin_id,
        admin=admin,
        settings=settings,
    )
    return {"data": updated}


@router.post(
    "/api/admin/reports/{report_id}/notes", status_code=status.HTTP_201_CREATED
)
def post_report_note_route(
    report_id: str,
    body: NoteRequest,
    admin: AdminContext = Depends(require_admin),
    settings: Settings = Depends(get_settings),
) -> dict:
    note = add_internal_note(
        report_id=report_id,
        content=body.content,
        admin=admin,
        settings=settings,
    )
    return {"data": note}


@router.post(
    "/api/admin/reports/{report_id}/message",
    status_code=status.HTTP_201_CREATED,
)
async def post_report_message_route(
    report_id: str,
    body: MessageRequest,
    admin: AdminContext = Depends(require_admin),
    settings: Settings = Depends(get_settings),
) -> dict:
    message = await send_reporter_message_and_notify(
        report_id=report_id,
        content=body.content,
        admin=admin,
        settings=settings,
    )
    return {"data": message}


@router.post(
    "/api/admin/reports/{report_id}/escalate",
    status_code=status.HTTP_201_CREATED,
)
def post_report_escalate_route(
    report_id: str,
    body: EscalateRequest,
    admin: AdminContext = Depends(require_admin),
    settings: Settings = Depends(get_settings),
) -> dict:
    result = escalate_report(
        report_id=report_id,
        escalation_contact_id=body.escalation_contact_id,
        admin=admin,
        settings=settings,
    )
    return {"data": result}


@router.post("/api/admin/reports/{report_id}/mark-false")
def post_report_mark_false_route(
    report_id: str,
    body: MarkFalseRequest = MarkFalseRequest(),
    admin: AdminContext = Depends(require_admin),
    settings: Settings = Depends(get_settings),
) -> dict:
    updated = mark_report_false(
        report_id=report_id,
        admin=admin,
        settings=settings,
        confirm_recusal_override=body.confirm_recusal_override,
    )
    return {"data": updated}


@router.delete(
    "/api/admin/reports/{report_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_report_route(
    report_id: str,
    body: DeleteReportRequest,
    admin: AdminContext = Depends(require_hoh),
    settings: Settings = Depends(get_settings),
) -> Response:
    delete_report_by_hoh(
        report_id=report_id,
        delete_reason=body.delete_reason,
        admin=admin,
        settings=settings,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
