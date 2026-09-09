"""Tests for POST /api/rate-limit/check and rate limit service logic."""

from unittest.mock import patch

import pytest
from app.exceptions.rate_limit import RateLimitExceededError
from app.main import create_app
from app.services.rate_limit import check_and_record_rate_limit
from fastapi.testclient import TestClient
from tests.conftest import FIXTURE_ACCESS_CODE

FIXTURE_HASH = "a" * 64


@pytest.fixture
def client(api_env: None) -> TestClient:
    return TestClient(create_app())


def _session_headers(client: TestClient) -> dict[str, str]:
    verify = client.post(
        "/api/access/verify",
        json={"access_code": FIXTURE_ACCESS_CODE},
        headers={"X-Session-Transport": "bearer"},
    )
    assert verify.status_code == 200
    token = verify.json()["session_token"]
    assert token
    return {"Authorization": f"Bearer {token}"}


def test_rate_limit_check_requires_session(client: TestClient) -> None:
    response = client.post(
        "/api/rate-limit/check",
        json={"channel": "telegram", "identifier_hash": FIXTURE_HASH},
    )
    assert response.status_code == 401


def test_rate_limit_check_rejects_invalid_hash(client: TestClient) -> None:
    headers = _session_headers(client)
    response = client.post(
        "/api/rate-limit/check",
        json={"channel": "telegram", "identifier_hash": "not-a-valid-hash"},
        headers=headers,
    )
    assert response.status_code == 422


@patch("app.services.rate_limit.fetch_entry_for_window", return_value=None)
@patch("app.services.rate_limit.insert_entry")
def test_rate_limit_check_allows_first_request(
    mock_insert,
    _mock_fetch,
    client: TestClient,
    api_env: None,
) -> None:
    headers = _session_headers(client)
    response = client.post(
        "/api/rate-limit/check",
        json={"channel": "telegram", "identifier_hash": FIXTURE_HASH},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json() == {"allowed": True}
    mock_insert.assert_called_once()


@patch("app.services.rate_limit.increment_entry")
@patch(
    "app.services.rate_limit.fetch_entry_for_window",
    return_value={"id": "00000000-0000-0000-0000-000000000001", "request_count": 20},
)
def test_rate_limit_check_returns_429_when_limit_reached(
    _mock_fetch,
    mock_increment,
    client: TestClient,
    api_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RATE_LIMIT_MAX_REQUESTS", "20")
    from app.core.settings import get_settings

    get_settings.cache_clear()
    headers = _session_headers(client)
    response = client.post(
        "/api/rate-limit/check",
        json={"channel": "telegram", "identifier_hash": FIXTURE_HASH},
        headers=headers,
    )
    assert response.status_code == 429
    assert response.json()["error"]["code"] == "rate_limit_exceeded"
    mock_increment.assert_not_called()


def test_check_and_record_rate_limit_increments_existing(
    api_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("RATE_LIMIT_MAX_REQUESTS", "5")
    from app.core.settings import get_settings

    get_settings.cache_clear()
    settings = get_settings()
    existing = {"id": "00000000-0000-0000-0000-000000000099", "request_count": 2}
    with (
        patch(
            "app.services.rate_limit.fetch_entry_for_window", return_value=existing
        ) as mock_fetch,
        patch("app.services.rate_limit.increment_entry") as mock_increment,
    ):
        check_and_record_rate_limit(
            channel="telegram",
            identifier_hash=FIXTURE_HASH,
            settings=settings,
        )
    mock_fetch.assert_called_once()
    mock_increment.assert_called_once_with(
        supabase_url=settings.supabase_url,
        service_role_key=settings.supabase_service_role_key,
        entry_id="00000000-0000-0000-0000-000000000099",
        request_count=3,
    )


def test_check_and_record_rate_limit_raises_when_at_cap(
    api_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("RATE_LIMIT_MAX_REQUESTS", "3")
    from app.core.settings import get_settings

    get_settings.cache_clear()
    settings = get_settings()
    existing = {"id": "entry-id", "request_count": 3}
    with (
        patch("app.services.rate_limit.fetch_entry_for_window", return_value=existing),
        patch("app.services.rate_limit.increment_entry") as mock_increment,
    ):
        with pytest.raises(RateLimitExceededError):
            check_and_record_rate_limit(
                channel="web",
                identifier_hash=FIXTURE_HASH,
                settings=settings,
            )
    mock_increment.assert_not_called()
