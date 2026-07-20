from datetime import UTC, datetime, timedelta

import pytest

from app.core.exceptions import ValidationError
from app.domain.connector.oauth import build_oauth_state, parse_oauth_state

SECRET = "unit-test-secret"


def test_roundtrip_preserves_context() -> None:
    state = build_oauth_state(
        secret_key=SECRET,
        company_id="c1",
        user_id="u1",
        provider="shopify",
        params={"shop": "minha-loja"},
    )
    payload = parse_oauth_state(state, secret_key=SECRET)
    assert payload.company_id == "c1"
    assert payload.user_id == "u1"
    assert payload.provider == "shopify"
    assert payload.params == {"shop": "minha-loja"}


def test_tampered_state_is_rejected() -> None:
    state = build_oauth_state(secret_key=SECRET, company_id="c1", user_id="u1", provider="ifood")
    body, signature = state.split(".", 1)
    tampered = f"{body}x.{signature}"
    with pytest.raises(ValidationError):
        parse_oauth_state(tampered, secret_key=SECRET)


def test_wrong_secret_is_rejected() -> None:
    state = build_oauth_state(secret_key=SECRET, company_id="c1", user_id="u1", provider="ifood")
    with pytest.raises(ValidationError):
        parse_oauth_state(state, secret_key="outro-secret")


def test_expired_state_is_rejected() -> None:
    past = datetime.now(UTC) - timedelta(hours=1)
    state = build_oauth_state(
        secret_key=SECRET, company_id="c1", user_id="u1", provider="ifood", now=past
    )
    with pytest.raises(ValidationError):
        parse_oauth_state(state, secret_key=SECRET)
