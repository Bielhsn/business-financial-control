"""Renovação do token OAuth antes que ele vença.

O `refresh_token` e o `expires_at` sempre foram gravados na conexão — e nunca
foram lidos. `OAuthTokens.is_expired()` e `GenericOAuth2Connector.refresh()`
existiam sem nenhum chamador: quando o token vencia, o provedor devolvia 401, a
conexão era marcada com erro e a sincronização parava. Pior que parar, a tela
continuava mostrando "Conectada" até alguém sincronizar à mão.

Fica separado da importação de vendas de propósito: `SyncConnectionUseCase` sabe
traduzir venda em lançamento e não precisa aprender o ciclo de vida de token.
Aqui é o contrário — este caso de uso não sabe nada sobre vendas.
"""

import json

from app.application.connector.oauth_flow import deserialize_tokens, serialize_tokens
from app.core.exceptions import ConnectorError
from app.core.logging import get_logger
from app.domain.connector.oauth import OAuthProvider
from app.domain.connector.ports import SecretCipher
from app.domain.connector.repository import ConnectionRepository

logger = get_logger(__name__)


class RefreshConnectionTokensUseCase:
    """Garante um access_token válido antes de usar a conexão.

    Devolve as credenciais já prontas para o conector — renovadas quando era
    preciso, intactas quando não era.
    """

    def __init__(
        self,
        connection_repository: ConnectionRepository,
        cipher: SecretCipher,
    ) -> None:
        self._connections = connection_repository
        self._cipher = cipher

    async def ensure_fresh(
        self,
        *,
        provider: str,
        secrets: dict[str, str],
        oauth_provider: OAuthProvider | None,
    ) -> dict[str, str]:
        # Conector de credenciais (Hotmart, iFood) não tem o que renovar: as
        # chaves não vencem. Sai cedo em vez de fingir um ciclo que não existe.
        if oauth_provider is None or "refresh_token" not in secrets:
            return secrets

        tokens = deserialize_tokens(json.dumps(secrets))
        # A folga do `is_expired` evita o caso em que o token passa na
        # verificação e vence no meio da sincronização seguinte.
        if not tokens.is_expired():
            return secrets
        if not tokens.refresh_token:
            # Sem refresh_token não há renovação silenciosa possível: quem
            # decide é o lojista, reconectando.
            raise ConnectorError(
                "A autorização com o provedor expirou. Reconecte a conta para continuar."
            )

        logger.info("oauth_token_refresh_started", provider=provider)
        try:
            renewed = await oauth_provider.refresh(refresh_token=tokens.refresh_token)
        except ConnectorError:
            logger.warning("oauth_token_refresh_failed", provider=provider)
            raise

        # Alguns provedores não devolvem um refresh_token novo na renovação —
        # nesse caso o antigo continua valendo, e descartá-lo quebraria a
        # próxima renovação.
        if renewed.refresh_token is None:
            renewed = type(renewed)(
                access_token=renewed.access_token,
                refresh_token=tokens.refresh_token,
                expires_at=renewed.expires_at,
                scope=renewed.scope or tokens.scope,
            )

        serialized = serialize_tokens(renewed)
        # Preserva a config existente: `upsert` reescreve a conexão inteira, e
        # passar um dicionário vazio apagaria o merchant_id/shop guardados na
        # conexão — a renovação do token derrubaria a integração que ela deveria
        # manter viva.
        connection = await self._connections.get_by_provider(provider)
        await self._connections.upsert(
            provider=provider,
            encrypted_secrets=self._cipher.encrypt(serialized),
            config=connection.config if connection else {},
        )
        logger.info("oauth_token_refreshed", provider=provider)
        return dict(json.loads(serialized))
