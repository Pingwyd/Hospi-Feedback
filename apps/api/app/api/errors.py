"""HTTP error envelope used by every API route."""

from fastapi import Request
from fastapi.responses import JSONResponse

from app.exceptions.access import AccessCodeRejectedError, AccessDeniedError
from app.exceptions.admin_reports import (
    AdminReportValidationError,
    HohRoleRequiredError,
    RecusalBlockedError,
    RecusalConfirmationRequiredError,
)
from app.exceptions.auth import (
    AdminLoginRejectedError,
    AdminSessionError,
    PermissionDeniedError,
)
from app.exceptions.base import AppError
from app.exceptions.rate_limit import RateLimitExceededError
from app.exceptions.reports import (
    AttachmentRejectedError,
    ReportClosedError,
    ReportNotFoundError,
)
from app.exceptions.telegram_admin import (
    TelegramAdminNotLinkedError,
    TelegramLinkRejectedError,
)


def error_body(code: str, message: str) -> dict[str, object]:
    return {"error": {"code": code, "message": message}}


def register_exception_handlers(app) -> None:
    @app.exception_handler(AccessDeniedError)
    async def _access_denied(_request: Request, exc: AccessDeniedError) -> JSONResponse:
        return JSONResponse(
            status_code=401,
            content=error_body("unauthorized", str(exc)),
        )

    @app.exception_handler(AccessCodeRejectedError)
    async def _access_code_rejected(
        _request: Request, exc: AccessCodeRejectedError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=401,
            content=error_body("unauthorized", str(exc)),
        )

    @app.exception_handler(AdminLoginRejectedError)
    async def _admin_login_rejected(
        _request: Request, exc: AdminLoginRejectedError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=401,
            content=error_body("unauthorized", str(exc)),
        )

    @app.exception_handler(AdminSessionError)
    async def _admin_session(_request: Request, exc: AdminSessionError) -> JSONResponse:
        return JSONResponse(
            status_code=401,
            content=error_body("unauthorized", str(exc)),
        )

    @app.exception_handler(PermissionDeniedError)
    async def _permission_denied(
        _request: Request, exc: PermissionDeniedError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=403,
            content=error_body("forbidden", str(exc)),
        )

    @app.exception_handler(ReportNotFoundError)
    async def _report_not_found(
        _request: Request, exc: ReportNotFoundError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content=error_body("not_found", str(exc)),
        )

    @app.exception_handler(ReportClosedError)
    async def _report_closed(_request: Request, exc: ReportClosedError) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content=error_body("conflict", str(exc)),
        )

    @app.exception_handler(AttachmentRejectedError)
    async def _attachment_rejected(
        _request: Request, exc: AttachmentRejectedError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=415,
            content=error_body("unsupported_media_type", str(exc)),
        )

    @app.exception_handler(TelegramLinkRejectedError)
    async def _telegram_link_rejected(
        _request: Request, exc: TelegramLinkRejectedError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=401,
            content=error_body("unauthorized", str(exc)),
        )

    @app.exception_handler(TelegramAdminNotLinkedError)
    async def _telegram_admin_not_linked(
        _request: Request, exc: TelegramAdminNotLinkedError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=403,
            content=error_body("forbidden", str(exc)),
        )

    @app.exception_handler(RateLimitExceededError)
    async def _rate_limit_exceeded(
        _request: Request, exc: RateLimitExceededError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=429,
            content=error_body("rate_limit_exceeded", str(exc)),
        )

    @app.exception_handler(RecusalBlockedError)
    async def _recusal_blocked(
        _request: Request, exc: RecusalBlockedError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content=error_body("recusal_blocked", str(exc)),
        )

    @app.exception_handler(RecusalConfirmationRequiredError)
    async def _recusal_confirmation_required(
        _request: Request, exc: RecusalConfirmationRequiredError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content=error_body("recusal_confirmation_required", str(exc)),
        )

    @app.exception_handler(HohRoleRequiredError)
    async def _hoh_role_required(
        _request: Request, exc: HohRoleRequiredError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=403,
            content=error_body("forbidden", str(exc)),
        )

    @app.exception_handler(AdminReportValidationError)
    async def _admin_report_validation(
        _request: Request, exc: AdminReportValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=error_body("validation_error", str(exc)),
        )

    @app.exception_handler(AppError)
    async def _app_error(_request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content=error_body("bad_request", str(exc)),
        )
