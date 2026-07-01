from functools import lru_cache
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEFAULT_SECRET_KEY = "changeme-generate-a-strong-random-secret"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: Literal["development", "staging", "production"] = "development"

    api_v1_prefix: str = "/api/v1"
    secret_key: str = _DEFAULT_SECRET_KEY

    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "business_financial_control"
    mongodb_server_selection_timeout_ms: int = 5000

    redis_url: str = "redis://localhost:6379/0"

    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    cors_allowed_origins: str = "http://localhost:5173"

    ai_provider: str = "anthropic"
    anthropic_api_key: str | None = None

    log_level: str = "INFO"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]

    @model_validator(mode="after")
    def _require_strong_secret_in_production(self) -> "Settings":
        if self.environment == "production" and self.secret_key == _DEFAULT_SECRET_KEY:
            raise ValueError("SECRET_KEY precisa ser definido com um valor forte em produção.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
