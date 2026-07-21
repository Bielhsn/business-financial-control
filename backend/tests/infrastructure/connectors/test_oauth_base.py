import httpx
import pytest

from app.core.exceptions import ConnectorError
from app.domain.connector.oauth import OAuthConfig
from app.infrastructure.connectors.oauth_base import GenericOAuth2Connector

pytestmark = pytest.mark.anyio

_CONFIG = OAuthConfig(
    authorize_url="https://auth.test/authorize",
    token_url="https://api.test/oauth/token",
    scopes=("read", "offline_access"),
    client_id_env="X_CLIENT_ID",
    client_secret_env="X_CLIENT_SECRET",
)


def _connector(handler: httpx.MockTransport) -> GenericOAuth2Connector:
    return GenericOAuth2Connector(
        provider="x",
        config=_CONFIG,
        client_id="the-client",
        client_secret="the-secret",
        transport=handler,
    )


def test_authorize_url_includes_all_params() -> None:
    connector = _connector(httpx.MockTransport(lambda req: httpx.Response(200)))
    url = connector.build_authorize_url(redirect_uri="https://app.test/cb", state="st4te")
    assert url.startswith("https://auth.test/authorize?")
    assert "response_type=code" in url
    assert "client_id=the-client" in url
    assert "state=st4te" in url
    assert "scope=read+offline_access" in url


def test_url_params_fill_placeholders() -> None:
    config = OAuthConfig(
        authorize_url="https://{shop}.myshopify.com/oauth/authorize",
        token_url="https://{shop}.myshopify.com/oauth/token",
        scopes=("read_orders",),
        client_id_env="S_ID",
        client_secret_env="S_SECRET",
    )
    connector = GenericOAuth2Connector(
        provider="shopify",
        config=config,
        client_id="cid",
        client_secret="sec",
        url_params={"shop": "minha-loja"},
        transport=httpx.MockTransport(lambda req: httpx.Response(200)),
    )
    url = connector.build_authorize_url(redirect_uri="https://app.test/cb", state="s")
    assert url.startswith("https://minha-loja.myshopify.com/oauth/authorize?")


async def test_exchange_code_parses_tokens() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == "https://api.test/oauth/token"
        return httpx.Response(
            200,
            json={
                "access_token": "acc",
                "refresh_token": "ref",
                "expires_in": 3600,
                "scope": "read",
            },
        )

    tokens = await _connector(httpx.MockTransport(handler)).exchange_code(
        code="abc", redirect_uri="https://app.test/cb"
    )
    assert tokens.access_token == "acc"
    assert tokens.refresh_token == "ref"
    assert tokens.expires_at is not None
    assert tokens.is_expired() is False


async def test_exchange_code_parses_camelcase_tokens() -> None:
    # O iFood responde em camelCase (accessToken/refreshToken/expiresIn).
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"accessToken": "acc", "refreshToken": "ref", "expiresIn": 21600},
        )

    tokens = await _connector(httpx.MockTransport(handler)).exchange_code(
        code="abc", redirect_uri="https://app.test/cb"
    )
    assert tokens.access_token == "acc"
    assert tokens.refresh_token == "ref"
    assert tokens.expires_at is not None


async def test_refresh_uses_refresh_grant() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        body = request.content.decode()
        assert "grant_type=refresh_token" in body
        return httpx.Response(200, json={"access_token": "new", "expires_in": 100})

    tokens = await _connector(httpx.MockTransport(handler)).refresh(refresh_token="ref")
    assert tokens.access_token == "new"


async def test_token_error_raises_connector_error() -> None:
    handler = httpx.MockTransport(lambda req: httpx.Response(401, json={"error": "invalid"}))
    with pytest.raises(ConnectorError):
        await _connector(handler).exchange_code(code="bad", redirect_uri="https://app.test/cb")


async def test_fetch_sales_not_yet_enabled() -> None:
    connector = _connector(httpx.MockTransport(lambda req: httpx.Response(200)))
    with pytest.raises(ConnectorError):
        await connector.fetch_sales({}, since=None)
