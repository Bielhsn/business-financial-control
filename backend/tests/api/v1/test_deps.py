import pytest

from app.api.v1.deps import (
    get_ai_provider,
    get_company_blueprint_repository,
    get_company_membership_repository,
    get_company_repository,
    get_password_hasher,
    get_refresh_token_repository,
    get_token_service,
    get_user_repository,
)
from app.core.config import Settings
from app.core.exceptions import AIProviderNotConfiguredError
from app.infrastructure.ai.anthropic_provider import AnthropicAIProvider
from app.infrastructure.repositories.company_blueprint_repository import (
    BeanieCompanyBlueprintRepository,
)
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


def test_get_company_blueprint_repository_returns_the_beanie_implementation() -> None:
    assert isinstance(get_company_blueprint_repository(), BeanieCompanyBlueprintRepository)


def test_get_ai_provider_returns_the_anthropic_implementation_when_configured() -> None:
    settings = Settings(_env_file=None, ai_provider="anthropic", anthropic_api_key="sk-test")

    assert isinstance(get_ai_provider(settings), AnthropicAIProvider)


def test_get_ai_provider_raises_when_api_key_is_missing() -> None:
    settings = Settings(_env_file=None, ai_provider="anthropic", anthropic_api_key=None)

    with pytest.raises(AIProviderNotConfiguredError):
        get_ai_provider(settings)


def test_get_ai_provider_raises_for_unsupported_provider() -> None:
    settings = Settings(_env_file=None, ai_provider="openai")

    with pytest.raises(AIProviderNotConfiguredError):
        get_ai_provider(settings)
