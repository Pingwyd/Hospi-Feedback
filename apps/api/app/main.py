from fastapi import FastAPI

from app.api.errors import register_exception_handlers
from app.api.routes.access import router as access_router
from app.api.routes.admin import router as admin_router
from app.api.routes.admin_audit import router as admin_audit_router
from app.api.routes.admin_config import router as admin_config_router
from app.api.routes.admin_dashboard import router as admin_dashboard_router
from app.api.routes.admin_management import router as admin_management_router
from app.api.routes.admin_reports import router as admin_reports_router
from app.api.routes.admin_telegram import router as admin_telegram_router
from app.api.routes.health import router as health_router
from app.api.routes.internal_jobs import router as internal_jobs_router
from app.api.routes.phase2 import router as phase2_router
from app.api.routes.rate_limit import router as rate_limit_router
from app.api.routes.reports import router as reports_router


def create_app() -> FastAPI:
    app = FastAPI(title="Hospi Feedback API", version="0.1.0")
    register_exception_handlers(app)
    app.include_router(health_router)
    app.include_router(access_router)
    app.include_router(admin_router)
    app.include_router(admin_reports_router)
    app.include_router(admin_config_router)
    app.include_router(admin_management_router)
    app.include_router(admin_audit_router)
    app.include_router(admin_dashboard_router)
    app.include_router(admin_telegram_router)
    app.include_router(internal_jobs_router)
    app.include_router(reports_router)
    app.include_router(rate_limit_router)
    app.include_router(phase2_router)
    return app


app = create_app()
