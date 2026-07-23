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

    # Autenticação (Etapa 27). require_email_verification desligado por padrão para
    # não travar dev/testes; em produção, ligue para exigir e-mail confirmado no login.
    require_email_verification: bool = False
    verification_code_ttl_minutes: int = 15
    password_reset_ttl_minutes: int = 30
    # Provedor de e-mail: "console" (dev — imprime o código no log) ou "resend"
    # (envia de verdade via API do Resend; exige RESEND_API_KEY).
    email_provider: str = "console"
    email_from: str = "Aurum OS <no-reply@aurum.local>"
    resend_api_key: str | None = None
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    # Google OAuth (login social). Sem client id, o endpoint responde 503.
    google_client_id: str | None = None

    # URL base pública da API — usada para montar o redirect_uri do OAuth das
    # integrações (o provedor redireciona o navegador de volta para cá).
    public_base_url: str = "http://localhost:8000"

    # Credenciais dos apps parceiros das integrações OAuth. Ficam vazias até o
    # dono da plataforma registrar cada app; sem elas, o provedor responde 503.
    mercadolivre_client_id: str | None = None
    mercadolivre_client_secret: str | None = None
    shopify_client_id: str | None = None
    shopify_client_secret: str | None = None
    ifood_client_id: str | None = None
    ifood_client_secret: str | None = None

    cors_allowed_origins: str = "http://localhost:5173"

    # E-mails com acesso ao painel administrativo do SaaS (super-admin), separados
    # por vírgula. Vazio = ninguém tem acesso (seguro por padrão).
    platform_admin_emails: str = ""

    # Senha opcional lida pelo script scripts/create_admin.py (variável de
    # ambiente ADMIN_PASSWORD). Nunca é usada pela API — só pelo bootstrap do
    # dono da plataforma. Fica None em operação normal.
    admin_password: str | None = None

    ai_provider: str = "anthropic"
    anthropic_api_key: str | None = None
    ai_model: str = "claude-sonnet-5"

    log_level: str = "INFO"

    # Chave para criptografar segredos de integrações em repouso (Fernet, base64
    # urlsafe de 32 bytes). Se ausente, é derivada de SECRET_KEY — defina uma
    # dedicada em produção para poder rotacionar sem invalidar sessões.
    connector_secret_key: str | None = None

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]

    @property
    def platform_admin_email_set(self) -> frozenset[str]:
        return frozenset(
            email.strip().lower()
            for email in self.platform_admin_emails.split(",")
            if email.strip()
        )

    def is_platform_admin(self, email: str) -> bool:
        return email.strip().lower() in self.platform_admin_email_set

    def oauth_client_credentials(
        self, client_id_env: str, client_secret_env: str
    ) -> tuple[str, str] | None:
        """Lê as credenciais de um app parceiro OAuth (ex.: MERCADOLIVRE_CLIENT_ID).
        Retorna None se qualquer uma estiver ausente."""
        client_id = getattr(self, client_id_env.lower(), None)
        client_secret = getattr(self, client_secret_env.lower(), None)
        if client_id and client_secret:
            return client_id, client_secret
        return None

    @model_validator(mode="after")
    def _require_strong_secret_in_production(self) -> "Settings":
        if self.environment == "production" and self.secret_key == _DEFAULT_SECRET_KEY:
            raise ValueError("SECRET_KEY precisa ser definido com um valor forte em produção.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
