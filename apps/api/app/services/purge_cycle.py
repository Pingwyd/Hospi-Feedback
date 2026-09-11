"""Scheduled report purge job using the unified archive_report() path."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from app.core.pdf_builder import build_purge_summary_pdf
from app.core.settings import Settings
from app.integrations.internal_jobs_store import list_reports_created_before
from app.integrations.reports_store import fetch_category_names_for_report
from app.services.report_archive import archive_report
from app.services.system_alerts import record_purge_pdf_delivery_failure
from app.services.telegram_delivery import deliver_purge_summary_pdf


def _store_kwargs(settings: Settings) -> dict[str, str]:
    return {
        "supabase_url": settings.supabase_url,
        "service_role_key": settings.supabase_service_role_key,
    }


def run_purge_cycle(*, settings: Settings) -> dict[str, Any]:
    """Archive reports past retention and deliver a summary PDF to HOH."""
    cutoff = datetime.now(tz=UTC) - timedelta(days=settings.report_retention_days)
    cutoff_iso = cutoff.isoformat().replace("+00:00", "Z")
    run_at = datetime.now(tz=UTC).isoformat().replace("+00:00", "Z")

    archived_summaries: list[dict[str, Any]] = []
    archived_ids: list[str] = []
    offset = 0
    batch_size = 100

    while True:
        candidates = list_reports_created_before(
            **_store_kwargs(settings),
            created_before_iso=cutoff_iso,
            limit=batch_size,
            offset=offset,
        )
        if not candidates:
            break
        for report in candidates:
            report_id = str(report["id"])
            categories = fetch_category_names_for_report(
                **_store_kwargs(settings),
                report_id=report_id,
            )
            archived_summaries.append(
                {
                    "id": report_id,
                    "report_type": report.get("report_type"),
                    "status": report.get("status"),
                    "created_at": report.get("created_at"),
                    "categories": categories,
                }
            )
            archive_report(
                report_id=report_id,
                archive_reason="scheduled_purge",
                settings=settings,
            )
            archived_ids.append(report_id)
        if len(candidates) < batch_size:
            break
        offset += batch_size

    pdf_bytes = build_purge_summary_pdf(
        run_at=run_at,
        archived_reports=archived_summaries,
    )
    delivered = deliver_purge_summary_pdf(
        settings=settings,
        pdf_bytes=pdf_bytes,
        archived_count=len(archived_ids),
    )
    pdf_delivery = "telegram" if delivered else "failed"
    if not delivered and archived_ids:
        record_purge_pdf_delivery_failure(settings=settings)

    return {
        "archived_count": len(archived_ids),
        "archived_report_ids": archived_ids,
        "pdf_delivery": pdf_delivery,
        "run_at": run_at,
    }
