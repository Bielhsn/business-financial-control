from app.api.v1.deps import (
    get_company_membership_repository,
    get_company_repository,
    get_password_hasher,
    get_refresh_token_repository,
    get_token_service,
    get_user_repository,
)
from app.core.config import Settings
from app.infrastructure.repositories.company_membership_repository import (
    BeanieCompanyMembershipRepository,
)
from app.infrastructure.repositories.company_repository import BeanieCompanyRepository
from app.infrastructure.repositories.refresh_token_repository import (
    BeanieRefreshTokenRepository,
)
from app.infrastructure.repositories.user_repository import BeanieUserRepository
from app.infrastructure.security.password import Argon2PasswordHasher
from app.infrastructure.security.tokens import JWTTokenService


def test_get_user_repository_returns_the_beanie_implementation() -> None:
    assert isinstance(get_user_repository(), BeanieUserRepository)


def test_get_refresh_token_repository_returns_the_beanie_implementation() -> None:
    assert isinstance(get_refresh_token_repository(), BeanieRefreshTokenRepository)


def test_get_password_hasher_returns_the_argon2_implementation() -> None:
    assert isinstance(get_password_hasher(), Argon2PasswordHasher)


def test_get_token_service_returns_the_jwt_implementation() -> None:
    assert isinstance(get_token_service(Settings(_env_file=None)), JWTTokenService)


def test_get_company_repository_returns_the_beanie_implementation() -> None:
    assert isinstance(get_company_repository(), BeanieCompanyRepository)


def test_get_company_membership_repository_returns_the_beanie_implementation() -> None:
    assert isinstance(get_company_membership_repository(), BeanieCompanyMembershipRepository)
