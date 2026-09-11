"""Internal job endpoints gated by X-Internal-Job-Secret."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import require_internal_job_secret
from app.core.settings import Settings, get_settings
from app.services.duplicate_scan import run_duplicate_scan
from app.services.escalation_export_purge import run_escalation_export_purge
from app.services.purge_cycle import run_purge_cycle

router = APIRouter(tags=["internal-jobs"])


@router.post("/internal/jobs/purge-cycle")
def post_purge_cycle(
    _secret: Annotated[None, Depends(require_internal_job_secret)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, object]:
    return run_purge_cycle(settings=settings)


@router.post("/internal/jobs/duplicate-scan")
def post_duplicate_scan(
    _secret: Annotated[None, Depends(require_internal_job_secret)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, object]:
    return run_duplicate_scan(settings=settings)


@router.post("/internal/jobs/purge-escalation-exports")
def post_purge_escalation_exports(
    _secret: Annotated[None, Depends(require_internal_job_secret)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, object]:
    return run_escalation_export_purge(settings=settings)
