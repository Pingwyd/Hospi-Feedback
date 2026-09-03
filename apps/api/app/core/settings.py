"""Process settings loaded from the environment. Fail fast on missing secrets."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "local"
    shared_access_code: str
    access_code_jwt_secret: str
    access_session_ttl_seconds: int = 86400
    access_cookie_name: str = "hospi_access_session"

    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str
    supabase_jwt_secret: str

    @property
    def cookie_secure(self) -> bool:
        env = self.environment.strip().lower()
        return env in {"staging", "stage", "production", "prod"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
