"""Purge expired escalation export files from the stricter-access bucket."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.core.settings import Settings
from app.integrations.escalations_store import (
    clear_escalation_export,
    list_expired_escalation_exports,
)
from app.integrations.supabase_storage import delete_object


def _store_kwargs(settings: Settings) -> dict[str, str]:
    return {
        "supabase_url": settings.supabase_url,
        "service_role_key": settings.supabase_service_role_key,
    }


def run_escalation_export_purge(*, settings: Settings) -> dict[str, Any]:
    """Delete export files past export_retention_until. Never touches report content."""
    now_iso = datetime.now(tz=UTC).isoformat().replace("+00:00", "Z")
    expired = list_expired_escalation_exports(
        **_store_kwargs(settings),
        expired_before_iso=now_iso,
    )
    purged: list[dict[str, str]] = []

    for row in expired:
        escalation_id = str(row["id"])
        file_path = str(row.get("exported_file_path") or "").strip()
        if not file_path:
            continue
        delete_object(
            supabase_url=settings.supabase_url,
            service_role_key=settings.supabase_service_role_key,
            bucket=settings.escalation_exports_bucket,
            object_path=file_path,
        )
        clear_escalation_export(
            **_store_kwargs(settings),
            escalation_id=escalation_id,
        )
        purged.append({"escalation_id": escalation_id, "exported_file_path": file_path})

    return {"purged_count": len(purged), "purged_exports": purged}
