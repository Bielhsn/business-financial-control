"""Renovação do token OAuth.

`refresh_token` e `expires_at` sempre foram gravados na conexão e nunca lidos:
`is_expired()` e `refresh()` existiam sem chamador. O token vencia, o provedor
devolvia 401, a conexão ia para erro — e a tela seguia dizendo "Conectada".
Estes testes existem para que esse silêncio não volte.
"""

import json
from datetime import UTC, datetime, timedelta

import pytest

from app.application.connector.oauth_flow import serialize_tokens
from app.application.connector.refresh_tokens import RefreshConnectionTokensUseCase
from app.core.exceptions import ConnectorError
from app.domain.connector.oauth import OAuthTokens
from tests.fakes import FakeConnectionRepository, FakeSecretCipher

pytestmark = pytest.mark.anyio


class FakeOAuthProvider:
    """Provedor OAuth de mentira: registra as renovações pedidas."""

    provider = "provedor_teste"

    def __init__(self, renewed: OAuthTokens | None = None, fail: bool = False) -> None:
        self._renewed = renewed
        self._fail = fail
        self.refresh_calls: list[str] = []

    def build_authorize_url(self, *, redirect_uri: str, state: str) -> str:  # pragma: no cover
        return ""

    async def exchange_code(self, *, code: str, redirect_uri: str) -> OAuthTokens:
        raise NotImplementedError  # pragma: no cover

    async def refresh(self, *, refresh_token: str) -> OAuthTokens:
        self.refresh_calls.append(refresh_token)
        if self._fail:
            raise ConnectorError("O provedor recusou a renovação.")
        assert self._renewed is not None
        return self._renewed


def _tokens(*, expira_em: timedelta, refresh: str | None = "refresh-antigo") -> dict[str, str]:
    return dict(
        json.loads(
            serialize_tokens(
                OAuthTokens(
                    access_token="token-velho",
                    refresh_token=refresh,
                    expires_at=datetime.now(UTC) + expira_em,
                    scope="read",
                )
            )
        )
    )


async def _use_case() -> tuple[RefreshConnectionTokensUseCase, FakeConnectionRepository]:
    repo = FakeConnectionRepository()
    await repo.upsert(provider="provedor_teste", encrypted_secrets="x", config={"shop": "loja"})
    return RefreshConnectionTokensUseCase(repo, FakeSecretCipher()), repo


async def test_valid_token_is_not_renewed() -> None:
    """Renovar sem necessidade gasta chamada e pode invalidar o token atual."""
    use_case, _ = await _use_case()
    provider = FakeOAuthProvider()

    secrets = _tokens(expira_em=timedelta(hours=2))
    result = await use_case.ensure_fresh(
        provider="provedor_teste", secrets=secrets, oauth_provider=provider
    )

    assert provider.refresh_calls == []
    assert result["access_token"] == "token-velho"


async def test_expired_token_is_renewed_and_persisted() -> None:
    use_case, repo = await _use_case()
    provider = FakeOAuthProvider(
        OAuthTokens(
            access_token="token-novo",
            refresh_token="refresh-novo",
            expires_at=datetime.now(UTC) + timedelta(hours=6),
            scope="read",
        )
    )

    result = await use_case.ensure_fresh(
        provider="provedor_teste",
        secrets=_tokens(expira_em=timedelta(hours=-1)),
        oauth_provider=provider,
    )

    assert provider.refresh_calls == ["refresh-antigo"]
    assert result["access_token"] == "token-novo"
    # Persistido: a próxima sincronização não pode renovar de novo.
    cifrado = await repo.get_encrypted_secrets("provedor_teste") or ""
    guardado = json.loads(FakeSecretCipher().decrypt(cifrado))
    assert guardado["access_token"] == "token-novo"


async def test_refresh_keeps_the_connection_config() -> None:
    """`upsert` reescreve a conexão inteira. Sem preservar a config, renovar o
    token apagaria o shop/merchant_id — a renovação derrubaria a integração que
    deveria manter viva."""
    use_case, repo = await _use_case()
    provider = FakeOAuthProvider(
        OAuthTokens(
            access_token="token-novo",
            refresh_token="refresh-novo",
            expires_at=datetime.now(UTC) + timedelta(hours=6),
            scope="read",
        )
    )

    await use_case.ensure_fresh(
        provider="provedor_teste",
        secrets=_tokens(expira_em=timedelta(hours=-1)),
        oauth_provider=provider,
    )

    conexao = await repo.get_by_provider("provedor_teste")
    assert conexao is not None
    assert conexao.config == {"shop": "loja"}


async def test_provider_that_omits_a_new_refresh_token_keeps_the_old_one() -> None:
    """Alguns provedores só devolvem o access_token na renovação. Descartar o
    refresh_token antigo quebraria a renovação seguinte."""
    use_case, _ = await _use_case()
    provider = FakeOAuthProvider(
        OAuthTokens(
            access_token="token-novo",
            refresh_token=None,
            expires_at=datetime.now(UTC) + timedelta(hours=6),
            scope=None,
        )
    )

    result = await use_case.ensure_fresh(
        provider="provedor_teste",
        secrets=_tokens(expira_em=timedelta(hours=-1)),
        oauth_provider=provider,
    )

    assert result["refresh_token"] == "refresh-antigo"


async def test_expired_without_refresh_token_asks_to_reconnect() -> None:
    use_case, _ = await _use_case()

    with pytest.raises(ConnectorError, match="Reconecte"):
        await use_case.ensure_fresh(
            provider="provedor_teste",
            secrets=_tokens(expira_em=timedelta(hours=-1), refresh=None),
            oauth_provider=FakeOAuthProvider(),
        )


async def test_credentials_connector_has_nothing_to_refresh() -> None:
    """Hotmart e iFood usam chaves que não vencem — não há ciclo a fingir."""
    use_case, _ = await _use_case()
    secrets = {"client_id": "abc", "client_secret": "xyz"}

    result = await use_case.ensure_fresh(provider="hotmart", secrets=secrets, oauth_provider=None)

    assert result == secrets
