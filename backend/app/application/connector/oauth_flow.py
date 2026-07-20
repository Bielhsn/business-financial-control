"""Orquestra o fluxo OAuth2 das integrações: iniciar (URL de autorização) e
concluir (trocar código por tokens e guardar a conexão criptografada)."""

import json
from datetime import UTC, datetime

from app.domain.connector.entities import Connection
from app.domain.connector.oauth import (
    OAuthProvider,
    OAuthTokens,
    build_oauth_state,
)
from app.domain.connector.ports import SecretCipher
from app.domain.connector.repository import ConnectionRepository

# Caminho fixo do callback registrado nos apps parceiros (redirect_uri).
OAUTH_CALLBACK_PATH = "/api/v1/connectors/oauth/callback"


def oauth_redirect_uri(public_base_url: str) -> str:
    return f"{public_base_url.rstrip('/')}{OAUTH_CALLBACK_PATH}"


def build_authorize_url(
    provider_obj: OAuthProvider,
    *,
    secret_key: str,
    company_id: str,
    user_id: str,
    provider: str,
    redirect_uri: str,
    params: dict[str, str] | None = None,
) -> str:
    state = build_oauth_state(
        secret_key=secret_key,
        company_id=company_id,
        user_id=user_id,
        provider=provider,
        params=params,
    )
    return provider_obj.build_authorize_url(redirect_uri=redirect_uri, state=state)


def serialize_tokens(tokens: OAuthTokens) -> str:
    return json.dumps(
        {
            "access_token": tokens.access_token,
            "refresh_token": tokens.refresh_token,
            "expires_at": tokens.expires_at.isoformat() if tokens.expires_at else None,
            "scope": tokens.scope,
        }
    )


def deserialize_tokens(raw: str) -> OAuthTokens:
    data = json.loads(raw)
    expires_at = data.get("expires_at")
    return OAuthTokens(
        access_token=data["access_token"],
        refresh_token=data.get("refresh_token"),
        expires_at=datetime.fromisoformat(expires_at) if expires_at else None,
        scope=data.get("scope"),
    )


class CompleteOAuthUseCase:
    """Troca o código de autorização por tokens e persiste a conexão. Os tokens
    ficam criptografados em repouso (mesma cifra dos demais segredos)."""

    def __init__(self, connection_repository: ConnectionRepository, cipher: SecretCipher) -> None:
        self._connections = connection_repository
        self._cipher = cipher

    async def execute(
        self,
        provider_obj: OAuthProvider,
        *,
        provider: str,
        code: str,
        redirect_uri: str,
        config: dict[str, str] | None = None,
    ) -> Connection:
        tokens = await provider_obj.exchange_code(code=code, redirect_uri=redirect_uri)
        encrypted = self._cipher.encrypt(serialize_tokens(tokens))
        stored_config = dict(config or {})
        stored_config["connected_at"] = datetime.now(UTC).isoformat()
        return await self._connections.upsert(
            provider=provider, encrypted_secrets=encrypted, config=stored_config
        )
