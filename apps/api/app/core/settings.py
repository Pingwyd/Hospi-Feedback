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
    report_attachments_bucket: str = "report-attachments"
    report_attachment_max_bytes: int = 5 * 1024 * 1024

    bot_service_secret: str = ""
    telegram_chat_id_encryption_key: str = ""
    telegram_identifier_pepper: str = ""
    rate_limit_window_seconds: int = 3600
    rate_limit_max_requests: int = 20
    telegram_link_code_ttl_seconds: int = 600

    @property
    def cookie_secure(self) -> bool:
        env = self.environment.strip().lower()
        return env in {"staging", "stage", "production", "prod"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
