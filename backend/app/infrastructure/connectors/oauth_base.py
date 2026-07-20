"""Cliente OAuth2 genérico (authorization-code) reutilizado por todos os
provedores OAuth.

Adicionar um provedor OAuth = uma linha no CONNECTOR_REGISTRY (com a OAuthConfig)
+ as variáveis de ambiente com client_id/secret. A dança do OAuth (URL de
autorização, troca de código, refresh) é a mesma para todos e vive aqui. O
mapeamento de vendas (`fetch_sales`) é específico de cada API e é adicionado por
subclasse quando as credenciais reais estiverem disponíveis para validação.
"""

from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

import httpx

from app.core.exceptions import ConnectorError
from app.domain.connector.entities import NormalizedSale
from app.domain.connector.oauth import OAuthConfig, OAuthTokens

_TIMEOUT = httpx.Timeout(20.0)


class GenericOAuth2Connector:
    """Implementa OAuthProvider para qualquer provedor descrito por uma
    OAuthConfig. `url_params` preenche placeholders como {shop} (Shopify)."""

    def __init__(
        self,
        *,
        provider: str,
        config: OAuthConfig,
        client_id: str,
        client_secret: str,
        url_params: dict[str, str] | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.provider = provider
        self._config = config
        self._client_id = client_id
        self._client_secret = client_secret
        self._url_params = url_params or {}
        self._transport = transport

    def _format(self, url: str) -> str:
        try:
            return url.format(**self._url_params)
        except KeyError as exc:
            raise ConnectorError(
                f"Parâmetro obrigatório ausente para {self.provider}: {exc}."
            ) from exc

    def build_authorize_url(self, *, redirect_uri: str, state: str) -> str:
        query = urlencode(
            {
                "response_type": "code",
                "client_id": self._client_id,
                "redirect_uri": redirect_uri,
                "scope": " ".join(self._config.scopes),
                "state": state,
            }
        )
        return f"{self._format(self._config.authorize_url)}?{query}"

    async def exchange_code(self, *, code: str, redirect_uri: str) -> OAuthTokens:
        return await self._token_request(
            {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": self._client_id,
                "client_secret": self._client_secret,
            }
        )

    async def refresh(self, *, refresh_token: str) -> OAuthTokens:
        return await self._token_request(
            {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": self._client_id,
                "client_secret": self._client_secret,
            }
        )

    async def _token_request(self, data: dict[str, str]) -> OAuthTokens:
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT, transport=self._transport) as client:
                response = await client.post(
                    self._format(self._config.token_url),
                    data=data,
                    headers={"Accept": "application/json"},
                )
        except httpx.HTTPError as exc:
            raise ConnectorError(f"Falha de rede ao autenticar em {self.provider}.") from exc

        if response.status_code >= 400:
            raise ConnectorError(
                f"{self.provider} recusou a autenticação (HTTP {response.status_code})."
            )
        payload = response.json()
        return _parse_token_payload(payload)

    async def fetch_sales(
        self, credentials: dict[str, str], *, since: datetime | None
    ) -> list[NormalizedSale]:
        # O mapeamento das vendas é específico de cada API e precisa de credenciais
        # reais para ser validado ponta a ponta. Fica pronto para ser implementado
        # por provedor sem tocar no fluxo de OAuth acima.
        raise ConnectorError(
            f"A sincronização de vendas de {self.provider} ainda não foi habilitada. "
            "Conclua o registro do app parceiro para ativar."
        )


def _parse_token_payload(payload: dict[str, object]) -> OAuthTokens:
    access_token = payload.get("access_token")
    if not isinstance(access_token, str):
        raise ConnectorError("Resposta de token sem access_token.")
    refresh_token = payload.get("refresh_token")
    expires_at: datetime | None = None
    expires_in = payload.get("expires_in")
    if isinstance(expires_in, int | float):
        expires_at = datetime.now(UTC) + timedelta(seconds=int(expires_in))
    scope = payload.get("scope")
    return OAuthTokens(
        access_token=access_token,
        refresh_token=refresh_token if isinstance(refresh_token, str) else None,
        expires_at=expires_at,
        scope=scope if isinstance(scope, str) else None,
    )
