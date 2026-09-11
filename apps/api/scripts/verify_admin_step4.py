"""Step 4 admin API verification (TestClient, mocked PostgREST).

Run from apps/api:
  python scripts/verify_admin_step4.py

Exit 0 when all checks pass. Does not require live Supabase.
"""

from __future__ import annotations

import os
import sys
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import patch

import jwt
from app.core.admin_auth import SUPABASE_JWT_ALG, SUPABASE_JWT_AUD
from app.core.settings import get_settings
from app.integrations.supabase_rest import AdminRecord
from app.main import create_app
from fastapi.testclient import TestClient

ADMIN_ID = "11111111-1111-1111-1111-111111111111"
OTHER_ADMIN_ID = "33333333-3333-3333-3333-333333333333"
REPORT_ID = "22222222-2222-2222-2222-222222222222"
CONTACT_ID = "44444444-4444-4444-4444-444444444444"
ESCALATION_ID = "55555555-5555-5555-5555-555555555555"
NOTE_ID = "66666666-6666-6666-6666-666666666666"
MESSAGE_ID = "77777777-7777-7777-7777-777777777777"

CHECKS: list[tuple[str, bool, str]] = []
AUDIT_ROWS: list[dict[str, Any]] = []


def record(name: str, passed: bool, detail: str = "") -> None:
    CHECKS.append((name, passed, detail))
    status = "PASS" if passed else "FAIL"
    suffix = f" ({detail})" if detail else ""
    print(f"[{status}] {name}{suffix}")


def _bootstrap_env() -> None:
    os.environ.setdefault("ENVIRONMENT", "local")
    os.environ.setdefault("SHARED_ACCESS_CODE", "unit-test-access-code-fixture")
    os.environ.setdefault(
        "ACCESS_CODE_JWT_SECRET", "verify-jwt-secret-not-for-production"
    )
    os.environ.setdefault("SUPABASE_URL", "http://127.0.0.1:54321")
    os.environ.setdefault("SUPABASE_ANON_KEY", "verify-anon")
    os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "verify-service-role")
    os.environ.setdefault("SUPABASE_JWT_SECRET", "verify-supabase-jwt-secret")
    os.environ.setdefault("ADMIN_2FA_REQUIRED", "true")
    get_settings.cache_clear()


def _admin_record() -> AdminRecord:
    return AdminRecord(
        id=ADMIN_ID,
        full_name="Ada Okonkwo",
        role="hoh",
        subunit=None,
        aliases=("Ada",),
        active=True,
    )


def _all_permissions() -> frozenset[str]:
    return frozenset(
        {
            "view",
            "respond",
            "assign",
            "close",
            "export",
            "manage_admins",
            "manage_categories",
            "manage_escalation_contacts",
        }
    )


def _issue_token() -> str:
    now = datetime.now(tz=UTC)
    payload = {
        "sub": ADMIN_ID,
        "role": "authenticated",
        "aud": SUPABASE_JWT_AUD,
        "iat": now,
        "exp": now + timedelta(hours=1),
    }
    return jwt.encode(
        payload,
        get_settings().supabase_jwt_secret,
        algorithm=SUPABASE_JWT_ALG,
    )


def _report_row(**overrides: Any) -> dict[str, Any]:
    row = {
        "id": REPORT_ID,
        "ticket_code_hash": "hash-fixture",
        "source": "web",
        "report_type": "complaint",
        "reported_member_name": "Someone else",
        "reported_member_admin_id": None,
        "description": "Step 4 verification report.",
        "incident_date": None,
        "incident_location": None,
        "severity": "medium",
        "status": "under_review",
        "assigned_admin_id": None,
        "publish_shoutout": False,
        "is_public": False,
        "possible_duplicate_of": None,
        "created_at": "2026-09-01T10:00:00Z",
        "updated_at": "2026-09-01T10:00:00Z",
    }
    row.update(overrides)
    return row


def _capture_audit(**kwargs: Any) -> dict[str, Any]:
    row_id = str(uuid.uuid4())
    row = {
        "id": row_id,
        "admin_id": kwargs["admin_id"],
        "report_id": kwargs.get("report_id"),
        "action": kwargs["action"],
        "detail": kwargs.get("detail"),
        "created_at": datetime.now(tz=UTC).isoformat(),
    }
    AUDIT_ROWS.append(row)
    return row


def _patch_report_fields(
    *,
    supabase_url: str,
    service_role_key: str,
    report_id: str,
    fields: dict[str, Any],
) -> dict[str, Any]:
    _ = (supabase_url, service_role_key, report_id)
    return _report_row(**fields)


def verify_lifecycle(client: TestClient, token: str) -> None:
    headers = {"Authorization": f"Bearer {token}"}

    list_response = client.get("/api/admin/reports", headers=headers)
    record(
        "Lifecycle: list reports",
        list_response.status_code == 200,
        f"status={list_response.status_code}",
    )

    detail_response = client.get(f"/api/admin/reports/{REPORT_ID}", headers=headers)
    record(
        "Lifecycle: view report detail",
        detail_response.status_code == 200,
        f"status={detail_response.status_code}",
    )

    assign_response = client.patch(
        f"/api/admin/reports/{REPORT_ID}/assign",
        headers=headers,
        json={"assigned_admin_id": OTHER_ADMIN_ID},
    )
    record(
        "Lifecycle: assign report",
        assign_response.status_code == 200,
        f"status={assign_response.status_code}",
    )

    message_response = client.post(
        f"/api/admin/reports/{REPORT_ID}/message",
        headers=headers,
        json={"content": "Admin follow-up message for reporter."},
    )
    record(
        "Lifecycle: chat with reporter",
        message_response.status_code in {200, 201},
        f"status={message_response.status_code}",
    )

    escalate_response = client.post(
        f"/api/admin/reports/{REPORT_ID}/escalate",
        headers=headers,
        json={"escalation_contact_id": CONTACT_ID},
    )
    record(
        "Lifecycle: escalate report",
        escalate_response.status_code in {200, 201},
        f"status={escalate_response.status_code}",
    )

    close_response = client.patch(
        f"/api/admin/reports/{REPORT_ID}/status",
        headers=headers,
        json={"status": "closed"},
    )
    record(
        "Lifecycle: close report",
        close_response.status_code == 200,
        f"status={close_response.status_code}",
    )

    expected_actions = ["assigned", "message_sent", "escalated", "closed"]
    actual_actions = [row["action"] for row in AUDIT_ROWS]
    record(
        "Audit log: lifecycle mutations recorded",
        actual_actions == expected_actions,
        f"expected={expected_actions}, actual={actual_actions}",
    )


def verify_recusal(
    client: TestClient,
    token: str,
    *,
    set_report: Any,
) -> None:
    headers = {"Authorization": f"Bearer {token}"}
    before = len(AUDIT_ROWS)

    set_report(
        reported_member_name="Ada Okonkwo",
        reported_member_admin_id=ADMIN_ID,
    )
    blocked = client.patch(
        f"/api/admin/reports/{REPORT_ID}/status",
        headers=headers,
        json={"status": "closed"},
    )
    record(
        "Recusal: blocked when linked to same admin",
        blocked.status_code == 409
        and blocked.json()["error"]["code"] == "recusal_blocked",
        f"status={blocked.status_code}",
    )

    blocked_audit = AUDIT_ROWS[before:]
    record(
        "Recusal: blocked attempt writes audit row",
        len(blocked_audit) == 1 and blocked_audit[0]["action"] == "other",
        f"rows={len(blocked_audit)}",
    )

    set_report(
        reported_member_name="Complaint about ada during hall meeting",
        reported_member_admin_id=None,
    )
    warn_before = len(AUDIT_ROWS)
    warn_without_confirm = client.patch(
        f"/api/admin/reports/{REPORT_ID}/status",
        headers=headers,
        json={"status": "closed", "confirm_recusal_override": False},
    )
    record(
        "Recusal: fuzzy match requires confirmation",
        warn_without_confirm.status_code == 409
        and warn_without_confirm.json()["error"]["code"]
        == "recusal_confirmation_required",
        f"status={warn_without_confirm.status_code}",
    )

    warn_with_confirm = client.patch(
        f"/api/admin/reports/{REPORT_ID}/status",
        headers=headers,
        json={"status": "closed", "confirm_recusal_override": True},
    )
    record(
        "Recusal: confirmed override closes report",
        warn_with_confirm.status_code == 200,
        f"status={warn_with_confirm.status_code}",
    )
    record(
        "Recusal: override writes closed audit row",
        any(row["action"] == "closed" for row in AUDIT_ROWS[warn_before + 1 :]),
        f"actions={[row['action'] for row in AUDIT_ROWS[warn_before + 1 :]]}",
    )


def verify_audit_viewer(client: TestClient, token: str) -> None:
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/admin/audit-log?limit=50", headers=headers)
    record(
        "Audit viewer: HOH can list audit log",
        response.status_code == 200 and "data" in response.json(),
        f"status={response.status_code}",
    )


def main() -> int:
    _bootstrap_env()
    app = create_app()
    client = TestClient(app)
    token = _issue_token()

    report_state = _report_row()

    def fetch_report_by_id(**kwargs: Any) -> dict[str, Any] | None:
        _ = kwargs
        return dict(report_state)

    def list_reports(**kwargs: Any) -> list[dict[str, Any]]:
        _ = kwargs
        return [dict(report_state)]

    def fetch_messages_for_report(**kwargs: Any) -> list[dict[str, Any]]:
        _ = kwargs
        return []

    def fetch_internal_notes_for_report(**kwargs: Any) -> list[dict[str, Any]]:
        _ = kwargs
        return []

    def insert_internal_note(**kwargs: Any) -> dict[str, Any]:
        _ = kwargs
        return {
            "id": NOTE_ID,
            "content": kwargs["content"],
            "created_at": "2026-09-09T10:00:00Z",
        }

    def insert_admin_message(**kwargs: Any) -> dict[str, Any]:
        _ = kwargs
        return {
            "id": MESSAGE_ID,
            "content": kwargs["content"],
            "created_at": "2026-09-09T10:01:00Z",
        }

    def insert_escalation(**kwargs: Any) -> dict[str, Any]:
        _ = kwargs
        return {"id": ESCALATION_ID, "report_id": REPORT_ID}

    def patch_fields(**kwargs: Any) -> dict[str, Any]:
        nonlocal report_state
        report_state = _patch_report_fields(**kwargs)
        return dict(report_state)

    def set_report(**overrides: Any) -> None:
        nonlocal report_state
        report_state = _report_row(**overrides)

    patches = [
        patch("app.core.admin_auth.fetch_active_admin", return_value=_admin_record()),
        patch(
            "app.core.admin_auth.fetch_admin_permissions",
            return_value=_all_permissions(),
        ),
        patch("app.services.audit_log.insert_audit_log_row", _capture_audit),
        patch("app.services.admin_reports.fetch_report_by_id", fetch_report_by_id),
        patch("app.services.admin_reports.list_reports", list_reports),
        patch(
            "app.services.admin_reports.fetch_messages_for_report",
            fetch_messages_for_report,
        ),
        patch(
            "app.services.admin_reports.fetch_internal_notes_for_report",
            fetch_internal_notes_for_report,
        ),
        patch("app.services.admin_reports.patch_report_fields", patch_fields),
        patch("app.services.admin_reports.insert_internal_note", insert_internal_note),
        patch("app.services.admin_reports.insert_admin_message", insert_admin_message),
        patch("app.services.admin_reports.insert_escalation", insert_escalation),
        patch(
            "app.services.admin_reports.broadcast_admin_event",
            return_value=None,
        ),
        patch(
            "app.services.admin_audit.list_audit_log_entries",
            return_value=AUDIT_ROWS,
        ),
    ]

    with (
        patches[0],
        patches[1],
        patches[2],
        patches[3],
        patches[4],
        patches[5],
        patches[6],
        patches[7],
        patches[8],
        patches[9],
        patches[10],
        patches[11],
        patches[12],
    ):
        verify_lifecycle(client, token)
        verify_recusal(client, token, set_report=set_report)
        verify_audit_viewer(client, token)

    print("\n--- Audit log captured during verification ---")
    for row in AUDIT_ROWS:
        print(
            f"- action={row['action']} report_id={row['report_id']} "
            f"detail={row.get('detail')}"
        )

    failed = [name for name, passed, _ in CHECKS if not passed]
    print(f"\n{len(CHECKS) - len(failed)}/{len(CHECKS)} checks passed.")
    if failed:
        print("Failed checks:")
        for name in failed:
            print(f"  - {name}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
