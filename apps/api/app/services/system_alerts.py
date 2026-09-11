"""Dashboard-visible operational alerts."""

from __future__ import annotations

from app.core.settings import Settings
from app.integrations.system_alerts_store import (
    SystemAlertsStoreError,
    insert_system_alert,
    list_active_system_alerts,
)

PURGE_PDF_UNDELIVERED = "purge_pdf_undelivered"


def _store_kwargs(settings: Settings) -> dict[str, str]:
    return {
        "supabase_url": settings.supabase_url,
        "service_role_key": settings.supabase_service_role_key,
    }


def create_system_alert(
    *,
    alert_type: str,
    message: str,
    settings: Settings,
) -> dict[str, object]:
    return insert_system_alert(
        **_store_kwargs(settings),
        alert_type=alert_type,
        message=message,
    )


def list_dashboard_alerts(*, settings: Settings) -> list[dict[str, object]]:
    """Return active alerts, or an empty list if the table is not migrated yet."""
    try:
        return list_active_system_alerts(**_store_kwargs(settings))
    except SystemAlertsStoreError:
        return []


def record_purge_pdf_delivery_failure(*, settings: Settings) -> dict[str, object]:
    return create_system_alert(
        alert_type=PURGE_PDF_UNDELIVERED,
        message=(
            "Last purge PDF could not be delivered. HOH has no linked Telegram account."
        ),
        settings=settings,
    )
