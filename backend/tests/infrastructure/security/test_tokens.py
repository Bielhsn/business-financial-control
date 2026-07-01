import time

import pytest

from app.core.config import Settings
from app.core.exceptions import UnauthorizedError
from app.infrastructure.security.tokens import JWTTokenService


def _service(**overrides: object) -> JWTTokenService:
    return JWTTokenService(Settings(_env_file=None, **overrides))  # type: ignore[arg-type]


def test_create_and_decode_access_token_roundtrip() -> None:
    service = _service()
    token = service.create_access_token("user-123")

    payload = service.decode_access_token(token)

    assert payload["sub"] == "user-123"


def test_decode_rejects_a_tampered_token() -> None:
    service = _service()
    token = service.create_access_token("user-123")

    with pytest.raises(UnauthorizedError):
        service.decode_access_token(token + "tampered")


def test_decode_rejects_an_expired_token() -> None:
    service = _service(access_token_expire_minutes=0)
    token = service.create_access_token("user-123")
    time.sleep(1)

    with pytest.raises(UnauthorizedError):
        service.decode_access_token(token)


def test_generate_refresh_token_returns_unique_high_entropy_values() -> None:
    service = _service()

    first = service.generate_refresh_token()
    second = service.generate_refresh_token()

    assert first != second
    assert len(first) > 32


def test_hash_refresh_token_is_deterministic() -> None:
    service = _service()
    raw_token = service.generate_refresh_token()

    assert service.hash_refresh_token(raw_token) == service.hash_refresh_token(raw_token)
