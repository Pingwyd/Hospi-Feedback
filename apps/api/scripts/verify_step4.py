"""Step 4 API verification (local TestClient, mocked PostgREST).

Run from apps/api:
  python scripts/verify_step4.py

Exit 0 when all checks pass. Does not require live Supabase.
Staging ownership-boundary re-run must be done separately when deployed.
"""

from __future__ import annotations

import io
import json
import os
import sys
from unittest.mock import patch

from app.core.settings import get_settings
from app.core.ticket_code import hash_ticket_code
from app.main import create_app
from fastapi.testclient import TestClient
from PIL import Image

FIXTURE_ACCESS_CODE = "unit-test-access-code-fixture"
TICKET_B = "EFGH6789"
TICKET_WRONG = "MNOP3456"
REPORT_B_ID = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
CREATED = "2026-09-03T12:00:00+00:00"

CHECKS: list[tuple[str, bool, str]] = []


def record(name: str, passed: bool, detail: str = "") -> None:
    CHECKS.append((name, passed, detail))
    status = "PASS" if passed else "FAIL"
    suffix = f" ({detail})" if detail else ""
    print(f"[{status}] {name}{suffix}")


def _png_bytes() -> bytes:
    image = Image.new("RGB", (2, 2), color="blue")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _bootstrap_env() -> None:
    os.environ.setdefault("ENVIRONMENT", "local")
    os.environ.setdefault("SHARED_ACCESS_CODE", FIXTURE_ACCESS_CODE)
    os.environ.setdefault(
        "ACCESS_CODE_JWT_SECRET", "verify-jwt-secret-not-for-production"
    )
    os.environ.setdefault("SUPABASE_URL", "http://127.0.0.1:54321")
    os.environ.setdefault("SUPABASE_ANON_KEY", "verify-anon")
    os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "verify-service-role")
    os.environ.setdefault("SUPABASE_JWT_SECRET", "verify-supabase-jwt-secret")
    get_settings.cache_clear()


def _report_row(report_id: str, ticket: str, *, status: str = "new") -> dict:
    return {
        "id": report_id,
        "status": status,
        "report_type": "complaint",
        "description": "Verification report body.",
        "reported_member_name": None,
        "severity": None,
        "created_at": CREATED,
        "updated_at": CREATED,
        "ticket_code_hash": hash_ticket_code(ticket),
    }


def verify_session_gate(client: TestClient) -> None:
    anonymous = client.post(
        "/api/reports",
        json={"report_type": "complaint", "description": "Should fail."},
    )
    record(
        "Session gate rejects submit without cookie",
        anonymous.status_code == 401,
        f"HTTP {anonymous.status_code}",
    )


def verify_full_lifecycle(client: TestClient) -> str:
    verify = client.post(
        "/api/access/verify",
        json={"access_code": FIXTURE_ACCESS_CODE},
    )
    record(
        "Access verify sets session",
        verify.status_code == 200,
        f"HTTP {verify.status_code}",
    )

    ticket = "ABCD2345"
    report_open = _report_row("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", ticket)
    report_closed = {**report_open, "status": "closed"}
    message_row = {
        "id": "cccccccc-cccc-cccc-cccc-cccccccccccc",
        "sender_type": "reporter",
        "content": "Follow-up",
        "created_at": CREATED,
    }

    with patch(
        "app.services.reporter_reports.generate_ticket_code", return_value=ticket
    ):
        with patch(
            "app.services.reporter_reports.insert_report", return_value=report_open
        ):
            with patch(
                "app.services.reporter_reports.fetch_report_by_ticket_hash",
                side_effect=[report_open, report_open, report_closed],
            ):
                with patch(
                    "app.services.reporter_reports.fetch_messages_for_report",
                    side_effect=[[], [message_row]],
                ):
                    with patch(
                        "app.services.reporter_reports.insert_reporter_message",
                        return_value=message_row,
                    ):
                        submit = client.post(
                            "/api/reports",
                            json={
                                "report_type": "complaint",
                                "description": "Verification report body.",
                            },
                        )
                        record(
                            "Submit report returns ticket code once",
                            submit.status_code == 201
                            and submit.json().get("ticket_code") == ticket,
                            json.dumps(submit.json()),
                        )

                        fetch = client.get(f"/api/reports/ticket/{ticket}")
                        record(
                            "Fetch status by ticket code",
                            fetch.status_code == 200,
                            f"HTTP {fetch.status_code}",
                        )

                        message = client.post(
                            f"/api/reports/ticket/{ticket}/message",
                            json={"content": "Follow-up"},
                        )
                        record(
                            "Reporter message while open",
                            message.status_code == 201,
                            f"HTTP {message.status_code}",
                        )

                        blocked = client.post(
                            f"/api/reports/ticket/{ticket}/message",
                            json={"content": "After close"},
                        )
                        record(
                            "Reporter message rejected when closed",
                            blocked.status_code == 409,
                            f"HTTP {blocked.status_code}",
                        )
    return ticket


def verify_cookie_cleared_mid_flow(client: TestClient) -> None:
    client.post("/api/access/verify", json={"access_code": FIXTURE_ACCESS_CODE})
    client.cookies.clear()
    denied = client.get("/api/_phase2/public-ping")
    record(
        "Protected route fails after cookie cleared",
        denied.status_code == 401,
        f"HTTP {denied.status_code}",
    )


def verify_attachment_ownership_boundary(client: TestClient) -> None:
    client.post("/api/access/verify", json={"access_code": FIXTURE_ACCESS_CODE})
    report_b = _report_row(REPORT_B_ID, TICKET_B)
    attachment_counts = {REPORT_B_ID: 0}

    def fetch_side_effect(*, ticket_code_hash: str, **_kwargs: object) -> dict | None:
        if ticket_code_hash == hash_ticket_code(TICKET_B):
            return report_b
        return None

    def insert_side_effect(*, report_id: str, **_kwargs: object) -> dict:
        attachment_counts[report_id] += 1
        return {
            "id": "dddddddd-dddd-dddd-dddd-dddddddddddd",
            "file_type": "image/png",
            "uploaded_at": CREATED,
        }

    with patch(
        "app.services.reporter_reports.fetch_report_by_ticket_hash",
        side_effect=fetch_side_effect,
    ):
        with patch("app.services.reporter_reports.upload_object"):
            with patch(
                "app.services.reporter_reports.insert_attachment",
                side_effect=insert_side_effect,
            ):
                wrong = client.post(
                    f"/api/reports/ticket/{TICKET_WRONG}/attachments",
                    files={"file": ("proof.png", _png_bytes(), "image/png")},
                )
                record(
                    "Wrong ticket code attachment returns 404",
                    wrong.status_code == 404,
                    f"HTTP {wrong.status_code}",
                )
                record(
                    "Wrong code created zero attachments",
                    attachment_counts[REPORT_B_ID] == 0,
                    f"count={attachment_counts[REPORT_B_ID]}",
                )

                ok = client.post(
                    f"/api/reports/ticket/{TICKET_B}/attachments",
                    files={"file": ("proof.png", _png_bytes(), "image/png")},
                )
                record(
                    "Correct ticket code attachment succeeds",
                    ok.status_code == 201,
                    f"HTTP {ok.status_code}",
                )


def main() -> int:
    _bootstrap_env()
    client = TestClient(create_app())

    print("=== Step 4 API verification (local) ===\n")
    verify_session_gate(client)
    verify_full_lifecycle(client)
    verify_cookie_cleared_mid_flow(client)
    verify_attachment_ownership_boundary(client)

    print("\n=== Summary ===")
    failed = [name for name, passed, _ in CHECKS if not passed]
    for name, passed, detail in CHECKS:
        print(f"  {'PASS' if passed else 'FAIL'}: {name}")
        if not passed and detail:
            print(f"         {detail}")

    print(f"\nTotal: {len(CHECKS) - len(failed)}/{len(CHECKS)} passed")
    if failed:
        print("Staging re-run still required when deployed.")
        return 1

    print("\nStaging: re-run attachment ownership-boundary on deployed API.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
