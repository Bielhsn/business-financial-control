from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.api.v1 import deps
from app.core.rate_limit import limiter
from app.main import app
from tests.fakes import (
    FakeAIProvider,
    FakeCompanyBlueprintRepository,
    FakeCompanyMembershipRepository,
    FakeCompanyRepository,
    FakeFinancialCategoryRepository,
    FakeFinancialTransactionRepository,
    FakePasswordHasher,
    FakeRefreshTokenRepository,
    FakeTokenService,
    FakeUserRepository,
)


@pytest.fixture
def fake_user_repository() -> FakeUserRepository:
    return FakeUserRepository()


@pytest.fixture
def fake_refresh_token_repository() -> FakeRefreshTokenRepository:
    return FakeRefreshTokenRepository()


@pytest.fixture
def fake_password_hasher() -> FakePasswordHasher:
    return FakePasswordHasher()


@pytest.fixture
def fake_token_service() -> FakeTokenService:
    return FakeTokenService()


@pytest.fixture
def fake_company_repository() -> FakeCompanyRepository:
    return FakeCompanyRepository()


@pytest.fixture
def fake_company_membership_repository() -> FakeCompanyMembershipRepository:
    return FakeCompanyMembershipRepository()


@pytest.fixture
def fake_company_blueprint_repository() -> FakeCompanyBlueprintRepository:
    return FakeCompanyBlueprintRepository()


@pytest.fixture
def fake_ai_provider() -> FakeAIProvider:
    return FakeAIProvider()


@pytest.fixture
def fake_financial_category_repository() -> FakeFinancialCategoryRepository:
    return FakeFinancialCategoryRepository()


@pytest.fixture
def fake_financial_transaction_repository() -> FakeFinancialTransactionRepository:
    return FakeFinancialTransactionRepository()


@pytest.fixture
def client(
    fake_user_repository: FakeUserRepository,
    fake_refresh_token_repository: FakeRefreshTokenRepository,
    fake_password_hasher: FakePasswordHasher,
    fake_token_service: FakeTokenService,
    fake_company_repository: FakeCompanyRepository,
    fake_company_membership_repository: FakeCompanyMembershipRepository,
    fake_company_blueprint_repository: FakeCompanyBlueprintRepository,
    fake_ai_provider: FakeAIProvider,
    fake_financial_category_repository: FakeFinancialCategoryRepository,
    fake_financial_transaction_repository: FakeFinancialTransactionRepository,
) -> Iterator[TestClient]:
    app.dependency_overrides[deps.get_user_repository] = lambda: fake_user_repository
    app.dependency_overrides[deps.get_refresh_token_repository] = (
        lambda: fake_refresh_token_repository
    )
    app.dependency_overrides[deps.get_password_hasher] = lambda: fake_password_hasher
    app.dependency_overrides[deps.get_token_service] = lambda: fake_token_service
    app.dependency_overrides[deps.get_company_repository] = lambda: fake_company_repository
    app.dependency_overrides[deps.get_company_membership_repository] = (
        lambda: fake_company_membership_repository
    )
    app.dependency_overrides[deps.get_company_blueprint_repository] = (
        lambda: fake_company_blueprint_repository
    )
    app.dependency_overrides[deps.get_ai_provider] = lambda: fake_ai_provider
    app.dependency_overrides[deps.get_financial_category_repository] = (
        lambda: fake_financial_category_repository
    )
    app.dependency_overrides[deps.get_financial_transaction_repository] = (
        lambda: fake_financial_transaction_repository
    )
    limiter.reset()

    # Sem "with": não dispara o lifespan (que exigiria um MongoDB real).
    yield TestClient(app)

    app.dependency_overrides.clear()
