import pytest

from app.application.auth.authenticate_user import AuthenticateUserUseCase
from app.application.auth.register_user import RegisterUserUseCase
from app.core.config import Settings
from app.core.exceptions import UnauthorizedError
from app.domain.user.entities import User
from tests.fakes import (
    FakePasswordHasher,
    FakeRefreshTokenRepository,
    FakeTokenService,
    FakeUserRepository,
)

pytestmark = pytest.mark.anyio


async def _register_user(
    user_repository: FakeUserRepository,
    password_hasher: FakePasswordHasher,
    email: str = "ana@example.com",
    password: str = "s3cr3t!!",
) -> User:
    return await RegisterUserUseCase(
        user_repository, password_hasher, Settings(_env_file=None)
    ).execute(email=email, password=password, full_name="Ana Silva")


def _use_case(
    user_repository: FakeUserRepository, password_hasher: FakePasswordHasher
) -> AuthenticateUserUseCase:
    return AuthenticateUserUseCase(
        user_repository,
        FakeRefreshTokenRepository(),
        password_hasher,
        FakeTokenService(),
        Settings(_env_file=None),
    )


async def test_authenticates_with_valid_credentials_and_issues_tokens() -> None:
    user_repository = FakeUserRepository()
    password_hasher = FakePasswordHasher()
    await _register_user(user_repository, password_hasher)

    token_pair = await _use_case(user_repository, password_hasher).execute(
        email="ANA@example.com", password="s3cr3t!!"
    )

    assert token_pair.access_token
    assert token_pair.refresh_token
    assert token_pair.token_type == "bearer"


async def test_rejects_wrong_password() -> None:
    user_repository = FakeUserRepository()
    password_hasher = FakePasswordHasher()
    await _register_user(user_repository, password_hasher)

    with pytest.raises(UnauthorizedError):
        await _use_case(user_repository, password_hasher).execute(
            email="ana@example.com", password="senha-errada"
        )


async def test_rejects_unknown_email() -> None:
    with pytest.raises(UnauthorizedError):
        await _use_case(FakeUserRepository(), FakePasswordHasher()).execute(
            email="ghost@example.com", password="qualquer"
        )


async def test_rejects_inactive_user() -> None:
    user_repository = FakeUserRepository()
    password_hasher = FakePasswordHasher()
    user = await _register_user(user_repository, password_hasher)
    user.is_active = False

    with pytest.raises(UnauthorizedError):
        await _use_case(user_repository, password_hasher).execute(
            email="ana@example.com", password="s3cr3t!!"
        )
