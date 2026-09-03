from fastapi import FastAPI

from app.api.errors import register_exception_handlers
from app.api.routes.access import router as access_router
from app.api.routes.admin import router as admin_router
from app.api.routes.phase2 import router as phase2_router


def create_app() -> FastAPI:
    app = FastAPI(title="Hospi Feedback API", version="0.1.0")
    register_exception_handlers(app)
    app.include_router(access_router)
    app.include_router(admin_router)
    app.include_router(phase2_router)
    return app


app = create_app()
