from datetime import date
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, File, UploadFile, status
from pydantic import BaseModel, Field

from app.api.deps import require_access_session
from app.core.settings import Settings, get_settings
from app.services.reporter_reports import (
    CreateReportInput,
    create_report,
    get_ticket_status,
    post_reporter_message,
    upload_report_attachment,
)

router = APIRouter(tags=["reports"])


class CreateReportRequest(BaseModel):
    report_type: Literal["complaint", "suggestion", "recognition"]
    description: str = Field(min_length=1)
    source: Literal["web", "telegram"] = "web"
    reported_member_name: str | None = None
    severity: Literal["low", "medium", "high"] | None = None
    incident_date: date | None = None
    incident_location: str | None = None
    category_ids: list[str] = Field(default_factory=list)


class CreateReportResponse(BaseModel):
    ticket_code: str
    status: str
    created_at: str


class MessageResponse(BaseModel):
    id: str
    sender_type: Literal["reporter", "admin"]
    content: str
    created_at: str


class TicketStatusResponse(BaseModel):
    status: str
    report_type: str
    description: str
    reported_member_name: str | None
    severity: str | None
    created_at: str
    updated_at: str
    messages: list[MessageResponse]


class ReporterMessageRequest(BaseModel):
    content: str = Field(min_length=1)


class AttachmentResponse(BaseModel):
    id: str
    file_type: str
    uploaded_at: str


# TODO(phase-3-followup): rate limit POST /api/reports
# TODO(phase-3-followup): rate limit GET /api/reports/ticket/{code}
@router.post(
    "/api/reports",
    response_model=CreateReportResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_report(
    body: CreateReportRequest,
    _session: Annotated[dict[str, Any], Depends(require_access_session)],
    settings: Settings = Depends(get_settings),
) -> CreateReportResponse:
    result = create_report(
        CreateReportInput(
            report_type=body.report_type,
            description=body.description,
            source=body.source,
            reported_member_name=body.reported_member_name,
            severity=body.severity,
            incident_date=body.incident_date,
            incident_location=body.incident_location,
            category_ids=tuple(body.category_ids),
        ),
        settings=settings,
    )
    return CreateReportResponse(
        ticket_code=result.ticket_code,
        status=result.status,
        created_at=result.created_at,
    )


# TODO(phase-3-followup): rate limit GET /api/reports/ticket/{code}
@router.get("/api/reports/ticket/{ticket_code}", response_model=TicketStatusResponse)
def fetch_ticket_status(
    ticket_code: str,
    _session: Annotated[dict[str, Any], Depends(require_access_session)],
    settings: Settings = Depends(get_settings),
) -> TicketStatusResponse:
    payload = get_ticket_status(ticket_code, settings=settings)
    return TicketStatusResponse(**payload)


# TODO(phase-3-followup): rate limit POST /api/reports/ticket/{code}/message
@router.post(
    "/api/reports/ticket/{ticket_code}/message",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def send_reporter_message(
    ticket_code: str,
    body: ReporterMessageRequest,
    _session: Annotated[dict[str, Any], Depends(require_access_session)],
    settings: Settings = Depends(get_settings),
) -> MessageResponse:
    payload = post_reporter_message(
        ticket_code,
        body.content,
        settings=settings,
    )
    return MessageResponse(**payload)


# TODO(phase-3-followup): rate limit POST /api/reports/ticket/{code}/attachments
@router.post(
    "/api/reports/ticket/{ticket_code}/attachments",
    response_model=AttachmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_ticket_attachment(
    ticket_code: str,
    _session: Annotated[dict[str, Any], Depends(require_access_session)],
    settings: Settings = Depends(get_settings),
    file: UploadFile = File(...),
) -> AttachmentResponse:
    file_bytes = await file.read()
    payload = upload_report_attachment(
        ticket_code,
        file_bytes,
        settings=settings,
    )
    return AttachmentResponse(**payload)
