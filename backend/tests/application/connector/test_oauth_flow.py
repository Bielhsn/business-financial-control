from datetime import UTC, datetime, timedelta

import pytest

from app.application.connector.oauth_flow import (
    CompleteOAuthUseCase,
    build_authorize_url,
    deserialize_tokens,
    oauth_redirect_uri,
    serialize_tokens,
)
from app.domain.connector.oauth import OAuthTokens, parse_oauth_state
from tests.fakes import FakeConnectionRepository, FakeSecretCipher

pytestmark = pytest.mark.anyio


class _FakeOAuthProvider:
    provider = "x"

    def build_authorize_url(self, *, redirect_uri: str, state: str) -> str:
        return f"https://auth.test/authorize?redirect_uri={redirect_uri}&state={state}"

    async def exchange_code(self, *, code: str, redirect_uri: str) -> OAuthTokens:
        return OAuthTokens(
            access_token=f"acc-for-{code}",
            refresh_token="ref",
            expires_at=datetime.now(UTC) + timedelta(hours=1),
            scope="read",
        )

    async def refresh(self, *, refresh_token: str) -> OAuthTokens:  # pragma: no cover
        raise NotImplementedError


def test_redirect_uri_is_built_from_base() -> None:
    assert oauth_redirect_uri("https://api.aurum.app/") == (
        "https://api.aurum.app/api/v1/connectors/oauth/callback"
    )


def test_token_serialization_roundtrip() -> None:
    tokens = OAuthTokens(
        access_token="a",
        refresh_token="r",
        expires_at=datetime(2026, 7, 20, 12, 0, tzinfo=UTC),
        scope="read",
    )
    restored = deserialize_tokens(serialize_tokens(tokens))
    assert restored == tokens


def test_authorize_url_carries_signed_state() -> None:
    url = build_authorize_url(
        _FakeOAuthProvider(),
        secret_key="s3cr3t",
        company_id="c1",
        user_id="u1",
        provider="x",
        redirect_uri="https://app.test/cb",
        params={"shop": "loja"},
    )
    state = url.split("state=", 1)[1]
    payload = parse_oauth_state(state, secret_key="s3cr3t")
    assert payload.company_id == "c1"
    assert payload.params == {"shop": "loja"}


async def test_complete_oauth_stores_encrypted_tokens() -> None:
    connections = FakeConnectionRepository()
    cipher = FakeSecretCipher()
    use_case = CompleteOAuthUseCase(connections, cipher)

    connection = await use_case.execute(
        _FakeOAuthProvider(),
        provider="x",
        code="the-code",
        redirect_uri="https://app.test/cb",
        config={"shop": "loja"},
    )

    assert connection.provider == "x"
    # Tokens ficam criptografados no repo (não em texto puro na entidade).
    stored = await connections.get_encrypted_secrets("x")
    assert stored is not None
    tokens = deserialize_tokens(cipher.decrypt(stored))
    assert tokens.access_token == "acc-for-the-code"
    assert connection.config["shop"] == "loja"
