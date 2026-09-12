"""Print Step 1 export sequence for HARD STOP 2 review.

Uses TestClient with mocked PostgREST. Run: python scripts/demo_admin_export.py
"""

from __future__ import annotations

from io import BytesIO
from unittest.mock import MagicMock, patch

import jwt
from app.core.admin_auth import SUPABASE_JWT_ALG, SUPABASE_JWT_AUD
from app.integrations.supabase_rest import AdminRecord
from app.main import create_app
from docx import Document
from fastapi.testclient import TestClient
FIXTURE_SUPABASE_JWT_SECRET = "unit-test-supabase-jwt-secret-not-for-production"

ADMIN_ID = "11111111-1111-1111-1111-111111111111"
REPORT_ID = "22222222-2222-2222-2222-222222222222"


def _token() -> str:
    from datetime import UTC, datetime, timedelta

    now = datetime.now(tz=UTC)
    payload = {
        "sub": ADMIN_ID,
        "role": "authenticated",
        "aud": SUPABASE_JWT_AUD,
        "iat": now,
        "exp": now + timedelta(hours=1),
    }
    return jwt.encode(payload, FIXTURE_SUPABASE_JWT_SECRET, algorithm=SUPABASE_JWT_ALG)


def _admin() -> AdminRecord:
    return AdminRecord(
        id=ADMIN_ID,
        full_name="Local Bootstrap HOH",
        role="hoh",
        subunit=None,
        aliases=("HOH",),
        active=True,
    )


def _report_row(*, status: str = "escalated", description: str = "Demo export row") -> dict:
    return {
        "id": REPORT_ID,
        "ticket_code_hash": "hash-not-exported",
        "source": "telegram",
        "report_type": "complaint",
        "reported_member_name": "Demo Member",
        "reported_member_admin_id": "33333333-3333-3333-3333-333333333333",
        "description": description,
        "incident_date": "2026-09-01",
        "incident_location": "Hall A",
        "severity": "high",
        "status": status,
        "assigned_admin_id": ADMIN_ID,
        "publish_shoutout": False,
        "is_public": False,
        "possible_duplicate_of": None,
        "created_at": "2026-09-01T10:00:00Z",
        "updated_at": "2026-09-02T12:00:00Z",
    }


def _print_step(title: str, method: str, path: str, response) -> None:
    print(f"\n=== {title} ===")
    print(f"{method} {path}")
    print(f"HTTP {response.status_code}")
    disposition = response.headers.get("content-disposition", "N/A")
    content_type = response.headers.get("content-type", "N/A")
    print(f"Content-Type: {content_type}")
    print(f"Content-Disposition: {disposition}")
    print(f"Body size: {len(response.content)} bytes")
    if response.content.startswith(b"%PDF"):
        print("Body prefix: %PDF (valid PDF)")
    elif response.content.startswith(b"PK"):
        print("Body prefix: PK (valid DOCX zip)")
    if response.status_code >= 400:
        print(response.json())


def main() -> None:
    import os

    from app.core.settings import get_settings

    os.environ.setdefault("ENVIRONMENT", "local")
    os.environ.setdefault("SHARED_ACCESS_CODE", "unit-test-access-code-fixture")
    os.environ.setdefault(
        "ACCESS_CODE_JWT_SECRET",
        "unit-test-jwt-secret-not-for-production",
    )
    os.environ.setdefault("SUPABASE_URL", "http://127.0.0.1:54321")
    os.environ.setdefault("SUPABASE_ANON_KEY", "unit-test-supabase-anon-key")
    os.environ.setdefault(
        "SUPABASE_SERVICE_ROLE_KEY",
        "unit-test-supabase-service-role-key",
    )
    os.environ.setdefault("SUPABASE_JWT_SECRET", FIXTURE_SUPABASE_JWT_SECRET)
    os.environ.setdefault("ADMIN_2FA_REQUIRED", "true")
    get_settings.cache_clear()

    client = TestClient(create_app())
    headers = {"Authorization": f"Bearer {_token()}"}

    with (
        patch("app.core.admin_auth.fetch_active_admin", return_value=_admin()),
        patch(
            "app.core.admin_auth.fetch_admin_permissions",
            return_value=frozenset({"view", "export"}),
        ),
        patch("app.services.admin_export.list_reports") as list_mock,
        patch(
            "app.services.admin_export.fetch_category_names_for_reports",
            return_value={REPORT_ID: ["Welfare"]},
        ),
        patch("app.services.admin_export.write_audit_log") as audit_mock,
    ):
        list_mock.side_effect = [
            [_report_row()],
            [_report_row(status="escalated")],
            [_report_row(description="Keyword welfare match")],
            [],
            [_report_row()],
        ]

        r1 = client.get("/api/admin/export", headers=headers)
        _print_step("1. Export all reports (PDF default)", "GET", "/api/admin/export", r1)

        r2 = client.get("/api/admin/export?status=escalated", headers=headers)
        _print_step(
            "2. Export with status filter",
            "GET",
            "/api/admin/export?status=escalated",
            r2,
        )

        r3 = client.get("/api/admin/export?keyword=welfare", headers=headers)
        _print_step(
            "3. Export with keyword filter",
            "GET",
            "/api/admin/export?keyword=welfare",
            r3,
        )

        r4 = client.get("/api/admin/export?status=closed", headers=headers)
        _print_step(
            "4. Export zero-result filter set",
            "GET",
            "/api/admin/export?status=closed",
            r4,
        )

        docx = client.get("/api/admin/export?format=docx", headers=headers)
        _print_step(
            "5. Export DOCX format",
            "GET",
            "/api/admin/export?format=docx",
            docx,
        )
        parsed = Document(BytesIO(docx.content))
        snippet = " | ".join(
            paragraph.text for paragraph in parsed.paragraphs[:8] if paragraph.text
        )
        print(f"DOCX preview: {snippet}")

        print("\n=== audit_log rows (mocked, one per request) ===")
        for index, call in enumerate(audit_mock.call_args_list, start=1):
            detail = call.kwargs["detail"]
            print(
                f"{index}. action={call.kwargs['action']!r} "
                f"report_id={call.kwargs['report_id']!r} "
                f"detail={detail}"
            )


if __name__ == "__main__":
    main()
