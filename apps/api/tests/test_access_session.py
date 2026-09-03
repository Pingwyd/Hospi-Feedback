from datetime import UTC, datetime, timedelta

import jwt
import pytest
from app.core.access_session import (
    ACCESS_TOKEN_ALG,
    ACCESS_TOKEN_TYP,
    issue_access_token,
)
from app.main import create_app
from fastapi.testclient import TestClient
from tests.conftest import FIXTURE_ACCESS_CODE, FIXTURE_ACCESS_JWT_SECRET


@pytest.fixture
def client(api_env: None) -> TestClient:
    return TestClient(create_app())


def test_verify_sets_httponly_cookie(client: TestClient) -> None:
    response = client.post(
        "/api/access/verify", json={"access_code": FIXTURE_ACCESS_CODE}
    )
    assert response.status_code == 200
    assert "hospi_access_session=" in response.headers.get("set-cookie", "")
    assert "HttpOnly" in response.headers.get("set-cookie", "")
    assert response.json()["session_token"] is None
    assert "sid" not in response.json()


def test_verify_rejects_wrong_code(client: TestClient) -> None:
    response = client.post("/api/access/verify", json={"access_code": "wrong-code"})
    assert response.status_code == 401
    assert "set-cookie" not in response.headers or "hospi_access_session=" not in (
        response.headers.get("set-cookie") or ""
    )


def test_public_ping_requires_session(client: TestClient) -> None:
    missing = client.get("/api/_phase2/public-ping")
    assert missing.status_code == 401

    expired_payload = {
        "iat": datetime.now(tz=UTC) - timedelta(hours=25),
        "exp": datetime.now(tz=UTC) - timedelta(hours=1),
        "sid": "00000000-0000-0000-0000-000000000001",
        "typ": ACCESS_TOKEN_TYP,
    }
    expired = jwt.encode(
        expired_payload, FIXTURE_ACCESS_JWT_SECRET, algorithm=ACCESS_TOKEN_ALG
    )
    expired_resp = client.get(
        "/api/_phase2/public-ping",
        headers={"Authorization": f"Bearer {expired}"},
    )
    assert expired_resp.status_code == 401


def test_public_ping_accepts_cookie_session(client: TestClient) -> None:
    verify = client.post(
        "/api/access/verify", json={"access_code": FIXTURE_ACCESS_CODE}
    )
    assert verify.status_code == 200
    ping = client.get("/api/_phase2/public-ping")
    assert ping.status_code == 200
    assert ping.json() == {"ok": True}


def test_issued_jwt_has_no_pii() -> None:
    token, _expires = issue_access_token(
        secret=FIXTURE_ACCESS_JWT_SECRET, ttl_seconds=60
    )
    claims = jwt.decode(token, FIXTURE_ACCESS_JWT_SECRET, algorithms=[ACCESS_TOKEN_ALG])
    assert set(claims.keys()) == {"iat", "exp", "sid", "typ"}
    assert claims["typ"] == ACCESS_TOKEN_TYP
