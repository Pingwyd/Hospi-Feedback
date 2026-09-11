"""Generate and store redacted escalation export PDFs."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.core.pdf_builder import build_escalation_export_pdf
from app.core.settings import Settings
from app.integrations.escalation_contacts_store import list_escalation_contacts
from app.integrations.escalations_store import patch_escalation_fields
from app.integrations.reports_store import fetch_category_names_for_report
from app.integrations.supabase_storage import upload_object


def _store_kwargs(settings: Settings) -> dict[str, str]:
    return {
        "supabase_url": settings.supabase_url,
        "service_role_key": settings.supabase_service_role_key,
    }


def _contact_name_map(settings: Settings) -> dict[str, str]:
    contacts = list_escalation_contacts(**_store_kwargs(settings))
    mapping: dict[str, str] = {}
    for contact in contacts:
        contact_id = str(contact.get("id") or "")
        name = str(contact.get("name") or "").strip()
        if contact_id and name:
            mapping[contact_id] = name
    return mapping


def generate_escalation_export(
    *,
    escalation_id: str,
    report: dict[str, object],
    escalation_contact_id: str,
    settings: Settings,
) -> dict[str, str]:
    """Build PDF, upload to stricter bucket, return path and retention timestamp."""
    report_id = str(report["id"])
    categories = fetch_category_names_for_report(
        **_store_kwargs(settings),
        report_id=report_id,
    )
    contact_name = _contact_name_map(settings).get(
        escalation_contact_id,
        "Escalation contact",
    )
    pdf_bytes = build_escalation_export_pdf(
        report=report,
        categories=categories,
        contact_name=contact_name,
    )
    object_path = f"{report_id}/{escalation_id}-{uuid4().hex}.pdf"
    upload_object(
        supabase_url=settings.supabase_url,
        service_role_key=settings.supabase_service_role_key,
        bucket=settings.escalation_exports_bucket,
        object_path=object_path,
        content=pdf_bytes,
        content_type="application/pdf",
    )
    retention_until = datetime.now(tz=UTC) + timedelta(
        days=settings.export_retention_days
    )
    retention_iso = retention_until.isoformat().replace("+00:00", "Z")
    patch_escalation_fields(
        **_store_kwargs(settings),
        escalation_id=escalation_id,
        fields={
            "exported_file_path": object_path,
            "export_retention_until": retention_iso,
        },
    )
    return {
        "exported_file_path": object_path,
        "export_retention_until": retention_iso,
    }
