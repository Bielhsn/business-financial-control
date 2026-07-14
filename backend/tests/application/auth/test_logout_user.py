from datetime import UTC, datetime, timedelta

import pytest

from app.application.auth.logout_user import LogoutUseCase
from tests.fakes import FakeRefreshTokenRepository, FakeTokenService

pytestmark = pytest.mark.anyio


async def test_logout_revokes_the_refresh_token() -> None:
    refresh_token_repository = FakeRefreshTokenRepository()
    token_service = FakeTokenService()
    raw_token = token_service.generate_refresh_token()
    stored = await refresh_token_repository.create(
        user_id="1",
        token_hash=token_service.hash_refresh_token(raw_token),
        expires_at=datetime.now(UTC) + timedelta(days=1),
    )

    await LogoutUseCase(refresh_token_repository, token_service).execute(
        raw_refresh_token=raw_token
    )

    revoked = await refresh_token_repository.get_by_token_hash(
        token_service.hash_refresh_token(raw_token)
    )
    assert revoked is not None
    assert revoked.revoked is True
    assert revoked.id == stored.id


async def test_logout_is_a_no_op_for_an_unknown_token() -> None:
    refresh_token_repository = FakeRefreshTokenRepository()
    token_service = FakeTokenService()

    await LogoutUseCase(refresh_token_repository, token_service).execute(
        raw_refresh_token="unknown"
    )
