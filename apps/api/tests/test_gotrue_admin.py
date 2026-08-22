import json
from email.message import EmailMessage
from io import BytesIO
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

import pytest
from app.exceptions.gotrue import GoTrueAdminError
from app.integrations.gotrue_admin import (
    create_confirmed_email_user,
    ensure_confirmed_email_user,
    find_user_id_by_email,
)


def _http_response(payload: dict, status: int = 200) -> MagicMock:
    response = MagicMock()
    response.status = status
    response.read.return_value = json.dumps(payload).encode("utf-8")
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    return response


@patch("app.integrations.gotrue_admin.urllib.request.urlopen")
def test_create_confirmed_email_user_returns_id(urlopen: MagicMock) -> None:
    urlopen.return_value = _http_response({"id": "usr_local_fixture"}, status=200)
    user_id = create_confirmed_email_user(
        supabase_url="http://127.0.0.1:54321",
        service_role_key="local-service-role-fixture",
        email="local-hoh@example.test",
        password="local-only-password-fixture",
    )
    assert user_id == "usr_local_fixture"


@patch("app.integrations.gotrue_admin.urllib.request.urlopen")
def test_find_user_id_by_email(urlopen: MagicMock) -> None:
    urlopen.return_value = _http_response(
        {"users": [{"id": "usr_found", "email": "local-hoh@example.test"}]}
    )
    found = find_user_id_by_email(
        supabase_url="http://127.0.0.1:54321",
        service_role_key="local-service-role-fixture",
        email="local-hoh@example.test",
    )
    assert found == "usr_found"


@patch(
    "app.integrations.gotrue_admin.find_user_id_by_email",
    return_value="usr_existing",
)
def test_ensure_reuses_existing_user(_find: MagicMock) -> None:
    user_id = ensure_confirmed_email_user(
        supabase_url="http://127.0.0.1:54321",
        service_role_key="local-service-role-fixture",
        email="local-hoh@example.test",
        password="local-only-password-fixture",
    )
    assert user_id == "usr_existing"


@patch("app.integrations.gotrue_admin.urllib.request.urlopen")
def test_create_user_http_error(urlopen: MagicMock) -> None:
    urlopen.side_effect = HTTPError(
        url="http://127.0.0.1:54321/auth/v1/admin/users",
        code=400,
        msg="Bad Request",
        hdrs=EmailMessage(),
        fp=BytesIO(b'{"error":"bad"}'),
    )
    with pytest.raises(GoTrueAdminError):
        create_confirmed_email_user(
            supabase_url="http://127.0.0.1:54321",
            service_role_key="local-service-role-fixture",
            email="local-hoh@example.test",
            password="local-only-password-fixture",
        )
