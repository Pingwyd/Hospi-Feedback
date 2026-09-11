"""Internal job endpoints: auth gates, purge cycle, duplicate scan."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from app.core.settings import get_settings
from app.main import create_app
from fastapi.testclient import TestClient

FIXTURE_INTERNAL_JOB_SECRET = "unit-test-internal-job-secret"
OLD_REPORT_ID = "11111111-1111-1111-1111-111111111111"
RECENT_REPORT_ID = "22222222-2222-2222-2222-222222222222"
DUPLICATE_CANDIDATE_ID = "33333333-3333-3333-3333-333333333333"
DUPLICATE_ORIGIN_ID = "44444444-4444-4444-4444-444444444444"
CATEGORY_ID = "55555555-5555-5555-5555-555555555555"


@pytest.fixture
def internal_job_env(api_env: None, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("X_INTERNAL_JOB_SECRET", FIXTURE_INTERNAL_JOB_SECRET)
    get_settings.cache_clear()


@pytest.fixture
def client(internal_job_env: None) -> TestClient:
    return TestClient(create_app())


def _old_report_row() -> dict[str, object]:
    old_created = (
        (datetime.now(tz=UTC) - timedelta(days=45)).isoformat().replace("+00:00", "Z")
    )
    return {
        "id": OLD_REPORT_ID,
        "ticket_code_hash": "hash-old",
        "source": "web",
        "report_type": "complaint",
        "reported_member_name": None,
        "reported_member_admin_id": None,
        "description": "Old report",
        "incident_date": None,
        "incident_location": None,
        "severity": "low",
        "status": "closed",
        "assigned_admin_id": None,
        "publish_shoutout": False,
        "is_public": False,
        "possible_duplicate_of": None,
        "created_at": old_created,
        "updated_at": old_created,
    }


def test_purge_cycle_missing_secret_returns_401_without_writes(
    client: TestClient,
) -> None:
    reports_before = 5
    reports_after = 5

    with (
        patch(
            "app.services.purge_cycle.archive_report",
        ) as archive_mock,
        patch(
            "app.integrations.internal_jobs_store.count_reports",
            side_effect=[reports_before, reports_after],
        ) as count_mock,
        patch(
            "app.integrations.internal_jobs_store.list_reports_created_before",
        ) as list_mock,
    ):
        response = client.post("/internal/jobs/purge-cycle")
        assert response.status_code == 401
        archive_mock.assert_not_called()
        list_mock.assert_not_called()
        count_mock.assert_not_called()
        assert reports_before == reports_after


def test_purge_cycle_wrong_secret_returns_401_without_writes(
    client: TestClient,
) -> None:
    with patch("app.services.purge_cycle.archive_report") as archive_mock:
        response = client.post(
            "/internal/jobs/purge-cycle",
            headers={"X-Internal-Job-Secret": "wrong-secret"},
        )
        assert response.status_code == 401
        archive_mock.assert_not_called()


def test_purge_cycle_unconfigured_secret_returns_503(
    api_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("X_INTERNAL_JOB_SECRET", raising=False)
    get_settings.cache_clear()
    client = TestClient(create_app())
    with patch("app.services.purge_cycle.archive_report") as archive_mock:
        response = client.post(
            "/internal/jobs/purge-cycle",
            headers={"X-Internal-Job-Secret": "any-value"},
        )
        assert response.status_code == 503
        archive_mock.assert_not_called()


def test_duplicate_scan_unconfigured_secret_returns_503(
    api_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("X_INTERNAL_JOB_SECRET", raising=False)
    get_settings.cache_clear()
    client = TestClient(create_app())
    with patch("app.services.duplicate_scan.run_duplicate_scan") as scan_mock:
        response = client.post(
            "/internal/jobs/duplicate-scan",
            headers={"X-Internal-Job-Secret": "any-value"},
        )
        assert response.status_code == 503
        scan_mock.assert_not_called()


def test_purge_cycle_archives_only_expired_reports(client: TestClient) -> None:
    old_report = _old_report_row()
    archived_calls: list[str] = []

    def fake_archive(*, report_id: str, **kwargs: object) -> str:
        archived_calls.append(report_id)
        return "archive-id"

    with (
        patch(
            "app.services.purge_cycle.list_reports_created_before",
            return_value=[old_report],
        ),
        patch(
            "app.services.purge_cycle.fetch_category_names_for_report",
            return_value=["Welfare"],
        ),
        patch("app.services.purge_cycle.archive_report", side_effect=fake_archive),
        patch(
            "app.services.purge_cycle.deliver_purge_summary_pdf",
            return_value=True,
        ),
        patch("app.services.purge_cycle.build_purge_summary_pdf", return_value=b"pdf"),
    ):
        response = client.post(
            "/internal/jobs/purge-cycle",
            headers={"X-Internal-Job-Secret": FIXTURE_INTERNAL_JOB_SECRET},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["archived_count"] == 1
    assert body["archived_report_ids"] == [OLD_REPORT_ID]
    assert body["pdf_delivery"] == "telegram"
    assert archived_calls == [OLD_REPORT_ID]


def test_purge_cycle_pdf_failure_creates_dashboard_alert(client: TestClient) -> None:
    with (
        patch(
            "app.services.purge_cycle.list_reports_created_before",
            return_value=[_old_report_row()],
        ),
        patch(
            "app.services.purge_cycle.fetch_category_names_for_report",
            return_value=[],
        ),
        patch("app.services.purge_cycle.archive_report", return_value="archive-id"),
        patch(
            "app.services.purge_cycle.deliver_purge_summary_pdf",
            return_value=False,
        ),
        patch(
            "app.services.purge_cycle.record_purge_pdf_delivery_failure"
        ) as alert_mock,
        patch("app.services.purge_cycle.build_purge_summary_pdf", return_value=b"pdf"),
    ):
        response = client.post(
            "/internal/jobs/purge-cycle",
            headers={"X-Internal-Job-Secret": FIXTURE_INTERNAL_JOB_SECRET},
        )

    assert response.status_code == 200
    assert response.json()["pdf_delivery"] == "failed"
    alert_mock.assert_called_once()


def test_duplicate_scan_flags_overlap_within_window(client: TestClient) -> None:
    now = datetime.now(tz=UTC)
    earlier_created = (now - timedelta(days=2)).isoformat().replace("+00:00", "Z")
    later_created = (now - timedelta(days=1)).isoformat().replace("+00:00", "Z")

    origin = {
        "id": DUPLICATE_ORIGIN_ID,
        "reported_member_name": "Alex Member",
        "created_at": earlier_created,
        "possible_duplicate_of": None,
    }
    candidate = {
        "id": DUPLICATE_CANDIDATE_ID,
        "reported_member_name": "alex member",
        "created_at": later_created,
        "possible_duplicate_of": None,
    }
    patch_calls: list[dict[str, object]] = []

    def fake_patch(*, report_id: str, fields: dict[str, object], **kwargs: object):
        patch_calls.append({"report_id": report_id, **fields})
        return {"id": report_id, **fields}

    with (
        patch(
            "app.services.duplicate_scan.list_reports_for_duplicate_scan",
            return_value=[origin, candidate],
        ),
        patch(
            "app.services.duplicate_scan.fetch_category_ids_for_reports",
            return_value={
                DUPLICATE_ORIGIN_ID: {CATEGORY_ID},
                DUPLICATE_CANDIDATE_ID: {CATEGORY_ID},
            },
        ),
        patch(
            "app.services.duplicate_scan.patch_report_fields",
            side_effect=fake_patch,
        ),
    ):
        response = client.post(
            "/internal/jobs/duplicate-scan",
            headers={"X-Internal-Job-Secret": FIXTURE_INTERNAL_JOB_SECRET},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["flagged_count"] == 1
    assert patch_calls == [
        {
            "report_id": DUPLICATE_CANDIDATE_ID,
            "possible_duplicate_of": DUPLICATE_ORIGIN_ID,
        }
    ]


def test_duplicate_scan_missing_secret_returns_401(client: TestClient) -> None:
    with patch(
        "app.services.duplicate_scan.patch_report_fields",
    ) as patch_mock:
        response = client.post("/internal/jobs/duplicate-scan")
        assert response.status_code == 401
        patch_mock.assert_not_called()


def test_duplicate_scan_links_younger_to_older_only_in_same_pass(
    client: TestClient,
) -> None:
    """Mutual matches in one run: only the later report is patched, never both."""
    now = datetime.now(tz=UTC)
    t1 = (now - timedelta(days=1)).isoformat().replace("+00:00", "Z")
    t2 = now.isoformat().replace("+00:00", "Z")
    report_a = {
        "id": DUPLICATE_ORIGIN_ID,
        "reported_member_name": "Same Person",
        "created_at": t1,
        "possible_duplicate_of": None,
    }
    report_b = {
        "id": DUPLICATE_CANDIDATE_ID,
        "reported_member_name": "Same Person",
        "created_at": t2,
        "possible_duplicate_of": None,
    }
    patched_ids: list[str] = []

    def fake_patch(*, report_id: str, fields: dict[str, object], **kwargs: object):
        patched_ids.append(report_id)
        return {"id": report_id, **fields}

    with (
        patch(
            "app.services.duplicate_scan.list_reports_for_duplicate_scan",
            return_value=[report_a, report_b],
        ),
        patch(
            "app.services.duplicate_scan.fetch_category_ids_for_reports",
            return_value={
                DUPLICATE_ORIGIN_ID: {CATEGORY_ID},
                DUPLICATE_CANDIDATE_ID: {CATEGORY_ID},
            },
        ),
        patch(
            "app.services.duplicate_scan.patch_report_fields",
            side_effect=fake_patch,
        ),
    ):
        response = client.post(
            "/internal/jobs/duplicate-scan",
            headers={"X-Internal-Job-Secret": FIXTURE_INTERNAL_JOB_SECRET},
        )

    assert response.status_code == 200
    assert patched_ids == [DUPLICATE_CANDIDATE_ID]


ESCALATION_ID = "66666666-6666-6666-6666-666666666666"
EXPORT_PATH = "11111111-1111-1111-1111-111111111111/escalation.pdf"


def test_purge_cycle_does_not_delete_escalation_exports(client: TestClient) -> None:
    """Report purge archives content but never touches escalation export storage."""
    with (
        patch(
            "app.services.purge_cycle.list_reports_created_before",
            return_value=[_old_report_row()],
        ),
        patch(
            "app.services.purge_cycle.fetch_category_names_for_report",
            return_value=[],
        ),
        patch("app.services.purge_cycle.archive_report", return_value="archive-id"),
        patch(
            "app.services.purge_cycle.deliver_purge_summary_pdf",
            return_value=True,
        ),
        patch("app.services.purge_cycle.build_purge_summary_pdf", return_value=b"pdf"),
        patch("app.services.escalation_export_purge.delete_object") as delete_mock,
        patch(
            "app.services.escalation_export_purge.list_expired_escalation_exports",
        ) as list_exports_mock,
    ):
        response = client.post(
            "/internal/jobs/purge-cycle",
            headers={"X-Internal-Job-Secret": FIXTURE_INTERNAL_JOB_SECRET},
        )

    assert response.status_code == 200
    delete_mock.assert_not_called()
    list_exports_mock.assert_not_called()


def test_escalation_export_purge_skips_active_retention(client: TestClient) -> None:
    with (
        patch(
            "app.services.escalation_export_purge.list_expired_escalation_exports",
            return_value=[],
        ),
        patch("app.services.escalation_export_purge.delete_object") as delete_mock,
        patch(
            "app.services.escalation_export_purge.clear_escalation_export",
        ) as clear_mock,
    ):
        response = client.post(
            "/internal/jobs/purge-escalation-exports",
            headers={"X-Internal-Job-Secret": FIXTURE_INTERNAL_JOB_SECRET},
        )

    assert response.status_code == 200
    assert response.json()["purged_count"] == 0
    delete_mock.assert_not_called()
    clear_mock.assert_not_called()


def test_escalation_export_purge_deletes_only_expired_exports(
    client: TestClient,
) -> None:
    expired_row = {
        "id": ESCALATION_ID,
        "report_id": OLD_REPORT_ID,
        "exported_file_path": EXPORT_PATH,
        "export_retention_until": "2020-01-01T00:00:00Z",
    }
    with (
        patch(
            "app.services.escalation_export_purge.list_expired_escalation_exports",
            return_value=[expired_row],
        ),
        patch("app.services.escalation_export_purge.delete_object") as delete_mock,
        patch(
            "app.services.escalation_export_purge.clear_escalation_export",
        ) as clear_mock,
        patch("app.services.purge_cycle.archive_report") as archive_mock,
    ):
        response = client.post(
            "/internal/jobs/purge-escalation-exports",
            headers={"X-Internal-Job-Secret": FIXTURE_INTERNAL_JOB_SECRET},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["purged_count"] == 1
    delete_mock.assert_called_once()
    clear_mock.assert_called_once()
    archive_mock.assert_not_called()


def test_escalation_export_purge_missing_secret_returns_401(
    client: TestClient,
) -> None:
    with patch("app.services.escalation_export_purge.delete_object") as delete_mock:
        response = client.post("/internal/jobs/purge-escalation-exports")
        assert response.status_code == 401
        delete_mock.assert_not_called()


def test_dashboard_stats_tolerates_missing_system_alerts_table(
    client: TestClient,
) -> None:
    from app.integrations.system_alerts_store import SystemAlertsStoreError
    from tests.test_admin_auth import ADMIN_ID, _issue_admin_token

    with (
        patch("app.core.admin_auth.fetch_active_admin") as fetch_admin_mock,
        patch("app.core.admin_auth.fetch_admin_permissions") as fetch_permissions_mock,
        patch("app.services.admin_dashboard.list_reports", return_value=[]),
        patch(
            "app.services.system_alerts.list_active_system_alerts",
            side_effect=SystemAlertsStoreError(
                "PostgREST GET failed with HTTP 404.",
                context={"status": 404},
            ),
        ),
    ):
        from app.integrations.supabase_rest import AdminRecord

        fetch_admin_mock.return_value = AdminRecord(
            id=ADMIN_ID,
            full_name="Local Bootstrap HOH",
            role="hoh",
            subunit=None,
            aliases=("HOH",),
            active=True,
        )
        fetch_permissions_mock.return_value = frozenset({"view"})
        response = client.get(
            "/api/admin/dashboard/stats",
            headers={"Authorization": f"Bearer {_issue_admin_token()}"},
        )

    assert response.status_code == 200
    assert response.json()["data"]["system_alerts"] == []
