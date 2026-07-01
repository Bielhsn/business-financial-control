from datetime import UTC, datetime, timedelta

import pytest

from app.application.auth.refresh_access_token import RefreshAccessTokenUseCase
from app.application.auth.token_issuer import issue_token_pair
from app.core.config import Settings
from app.core.exceptions import UnauthorizedError
from tests.fakes import FakeRefreshTokenRepository, FakeTokenService, FakeUserRepository

pytestmark = pytest.mark.anyio


async def test_rotates_refresh_token_and_issues_a_new_pair() -> None:
    user_repository = FakeUserRepository()
    refresh_token_repository = FakeRefreshTokenRepository()
    token_service = FakeTokenService()
    settings = Settings(_env_file=None)
    user = await user_repository.create(
        email="ana@example.com", hashed_password="x", full_name="Ana"
    )

    initial_pair = await issue_token_pair(
        user_id=user.id,
        refresh_token_repository=refresh_token_repository,
        token_service=token_service,
        settings=settings,
    )

    use_case = RefreshAccessTokenUseCase(
        user_repository, refresh_token_repository, token_service, settings
    )
    new_pair = await use_case.execute(raw_refresh_token=initial_pair.refresh_token)

    assert new_pair.refresh_token != initial_pair.refresh_token

    with pytest.raises(UnauthorizedError):
        await use_case.execute(raw_refresh_token=initial_pair.refresh_token)


async def test_rejects_unknown_refresh_token() -> None:
    use_case = RefreshAccessTokenUseCase(
        FakeUserRepository(),
        FakeRefreshTokenRepository(),
        FakeTokenService(),
        Settings(_env_file=None),
    )

    with pytest.raises(UnauthorizedError):
        await use_case.execute(raw_refresh_token="does-not-exist")


async def test_rejects_expired_refresh_token() -> None:
    user_repository = FakeUserRepository()
    refresh_token_repository = FakeRefreshTokenRepository()
    token_service = FakeTokenService()
    settings = Settings(_env_file=None)
    user = await user_repository.create(
        email="ana@example.com", hashed_password="x", full_name="Ana"
    )

    raw_token = token_service.generate_refresh_token()
    await refresh_token_repository.create(
        user_id=user.id,
        token_hash=token_service.hash_refresh_token(raw_token),
        expires_at=datetime.now(UTC) - timedelta(seconds=1),
    )

    use_case = RefreshAccessTokenUseCase(
        user_repository, refresh_token_repository, token_service, settings
    )

    with pytest.raises(UnauthorizedError):
        await use_case.execute(raw_refresh_token=raw_token)


async def test_rejects_refresh_token_of_inactive_user() -> None:
    user_repository = FakeUserRepository()
    refresh_token_repository = FakeRefreshTokenRepository()
    token_service = FakeTokenService()
    settings = Settings(_env_file=None)
    user = await user_repository.create(
        email="ana@example.com", hashed_password="x", full_name="Ana"
    )

    pair = await issue_token_pair(
        user_id=user.id,
        refresh_token_repository=refresh_token_repository,
        token_service=token_service,
        settings=settings,
    )
    user.is_active = False

    use_case = RefreshAccessTokenUseCase(
        user_repository, refresh_token_repository, token_service, settings
    )

    with pytest.raises(UnauthorizedError):
        await use_case.execute(raw_refresh_token=pair.refresh_token)
