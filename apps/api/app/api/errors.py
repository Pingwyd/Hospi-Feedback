"""HTTP error envelope used by every API route."""

from fastapi import Request
from fastapi.responses import JSONResponse

from app.exceptions.access import AccessCodeRejectedError, AccessDeniedError
from app.exceptions.auth import (
    AdminLoginRejectedError,
    AdminSessionError,
    PermissionDeniedError,
)
from app.exceptions.base import AppError


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

    @app.exception_handler(AppError)
    async def _app_error(_request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content=error_body("bad_request", str(exc)),
        )
