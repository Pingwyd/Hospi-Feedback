"""Print Step 1 reporter API sequence for HARD STOP 2 review.

Uses TestClient with mocked PostgREST. Run: python scripts/demo_reporter_flow.py
"""

from __future__ import annotations

import json
from unittest.mock import patch

from app.core.ticket_code import hash_ticket_code
from app.main import create_app
from fastapi.testclient import TestClient

FIXTURE_ACCESS_CODE = "unit-test-access-code-fixture"

TICKET = "ABCD2345"
REPORT_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
CREATED = "2026-09-03T12:00:00+00:00"


def _print_step(title: str, method: str, path: str, response) -> None:
    print(f"\n=== {title} ===")
    print(f"{method} {path}")
    print(f"HTTP {response.status_code}")
    print(json.dumps(response.json(), indent=2))


def main() -> None:
    import os

    os.environ.setdefault("ENVIRONMENT", "local")
    os.environ.setdefault("SHARED_ACCESS_CODE", FIXTURE_ACCESS_CODE)
    os.environ.setdefault(
        "ACCESS_CODE_JWT_SECRET", "demo-jwt-secret-not-for-production-use"
    )
    os.environ.setdefault("SUPABASE_URL", "http://127.0.0.1:54321")
    os.environ.setdefault("SUPABASE_ANON_KEY", "demo-anon")
    os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "demo-service-role")
    os.environ.setdefault("SUPABASE_JWT_SECRET", "demo-supabase-jwt-secret")
    from app.core.settings import get_settings

    get_settings.cache_clear()

    ticket_hash = hash_ticket_code(TICKET)
    report_open = {
        "id": REPORT_ID,
        "status": "new",
        "report_type": "complaint",
        "description": "Noise during quiet hours.",
        "reported_member_name": None,
        "severity": "medium",
        "created_at": CREATED,
        "updated_at": CREATED,
        "ticket_code_hash": ticket_hash,
    }
    report_closed = {**report_open, "status": "closed"}
    message_row = {
        "id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        "sender_type": "reporter",
        "content": "Any update?",
        "created_at": CREATED,
    }

    with patch(
        "app.services.reporter_reports.generate_ticket_code", return_value=TICKET
    ):
        with patch(
            "app.services.reporter_reports.insert_report",
            return_value=report_open,
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
                        client = TestClient(create_app())
                        verify = client.post(
                            "/api/access/verify",
                            json={"access_code": FIXTURE_ACCESS_CODE},
                        )
                        _print_step(
                            "1. Access verify",
                            "POST",
                            "/api/access/verify",
                            verify,
                        )
                        submit = client.post(
                            "/api/reports",
                            json={
                                "report_type": "complaint",
                                "description": "Noise during quiet hours.",
                                "severity": "medium",
                            },
                        )
                        _print_step(
                            "2. Submit report",
                            "POST",
                            "/api/reports",
                            submit,
                        )
                        fetch = client.get(f"/api/reports/ticket/{TICKET}")
                        _print_step(
                            "3. Fetch by ticket",
                            "GET",
                            f"/api/reports/ticket/{TICKET}",
                            fetch,
                        )
                        message = client.post(
                            f"/api/reports/ticket/{TICKET}/message",
                            json={"content": "Any update?"},
                        )
                        _print_step(
                            "4. Reporter message (open)",
                            "POST",
                            f"/api/reports/ticket/{TICKET}/message",
                            message,
                        )
                        print("\n=== 5. Close report (TEST-ONLY PostgREST) ===")
                        print(
                            "PATCH /rest/v1/reports?id=eq."
                            f"{REPORT_ID}  body={{'status':'closed'}}"
                        )
                        print(
                            "Replace with Phase 4 PATCH /api/admin/reports/{id}/status"
                        )
                        blocked = client.post(
                            f"/api/reports/ticket/{TICKET}/message",
                            json={"content": "After close."},
                        )
                        _print_step(
                            "6. Reporter message (closed)",
                            "POST",
                            f"/api/reports/ticket/{TICKET}/message",
                            blocked,
                        )


if __name__ == "__main__":
    main()
