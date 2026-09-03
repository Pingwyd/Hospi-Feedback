import pytest
from app.core.settings import get_settings

FIXTURE_ACCESS_CODE = "unit-test-access-code-fixture"
FIXTURE_ACCESS_JWT_SECRET = "unit-test-jwt-secret-not-for-production"
FIXTURE_SUPABASE_URL = "http://127.0.0.1:54321"
FIXTURE_SUPABASE_ANON_KEY = "unit-test-supabase-anon-key"
FIXTURE_SUPABASE_SERVICE_ROLE_KEY = "unit-test-supabase-service-role-key"
FIXTURE_SUPABASE_JWT_SECRET = "unit-test-supabase-jwt-secret-not-for-production"


@pytest.fixture
def api_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "local")
    monkeypatch.setenv("SHARED_ACCESS_CODE", FIXTURE_ACCESS_CODE)
    monkeypatch.setenv("ACCESS_CODE_JWT_SECRET", FIXTURE_ACCESS_JWT_SECRET)
    monkeypatch.setenv("SUPABASE_URL", FIXTURE_SUPABASE_URL)
    monkeypatch.setenv("SUPABASE_ANON_KEY", FIXTURE_SUPABASE_ANON_KEY)
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", FIXTURE_SUPABASE_SERVICE_ROLE_KEY)
    monkeypatch.setenv("SUPABASE_JWT_SECRET", FIXTURE_SUPABASE_JWT_SECRET)
    get_settings.cache_clear()
