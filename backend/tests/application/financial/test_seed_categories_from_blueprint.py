import pytest

from app.application.financial.create_category import CreateFinancialCategoryUseCase
from app.application.financial.seed_categories_from_blueprint import (
    SeedFinancialCategoriesFromBlueprintUseCase,
)
from app.core.exceptions import NotFoundError
from app.domain.blueprint.entities import SuggestedFinancialCategory
from app.domain.financial.entities import FinancialCategoryType
from tests.fakes import FakeCompanyBlueprintRepository, FakeFinancialCategoryRepository

pytestmark = pytest.mark.anyio


async def _seed_blueprint(blueprint_repository: FakeCompanyBlueprintRepository) -> None:
    await blueprint_repository.upsert(
        company_id="company-1",
        modules=["financial_core"],
        financial_categories=[
            SuggestedFinancialCategory(name="Vendas", type=FinancialCategoryType.INCOME),
            SuggestedFinancialCategory(name="Aluguel", type=FinancialCategoryType.EXPENSE),
        ],
        kpis=[],
        client_custom_fields=[],
        ai_provider="anthropic",
    )


async def test_creates_categories_from_the_blueprint_suggestions() -> None:
    blueprint_repository = FakeCompanyBlueprintRepository()
    await _seed_blueprint(blueprint_repository)
    category_repository = FakeFinancialCategoryRepository()

    created = await SeedFinancialCategoriesFromBlueprintUseCase(
        blueprint_repository, category_repository
    ).execute(company_id="company-1")

    assert {c.name for c in created} == {"Vendas", "Aluguel"}
    assert len(await category_repository.list_all(only_active=False)) == 2


async def test_seeding_twice_does_not_duplicate_categories() -> None:
    blueprint_repository = FakeCompanyBlueprintRepository()
    await _seed_blueprint(blueprint_repository)
    category_repository = FakeFinancialCategoryRepository()
    use_case = SeedFinancialCategoriesFromBlueprintUseCase(
        blueprint_repository, category_repository
    )

    await use_case.execute(company_id="company-1")
    second_run = await use_case.execute(company_id="company-1")

    assert second_run == []
    assert len(await category_repository.list_all(only_active=False)) == 2


async def test_skips_categories_that_already_exist() -> None:
    blueprint_repository = FakeCompanyBlueprintRepository()
    await _seed_blueprint(blueprint_repository)
    category_repository = FakeFinancialCategoryRepository()
    await CreateFinancialCategoryUseCase(category_repository).execute(
        name="Vendas", type=FinancialCategoryType.INCOME
    )

    created = await SeedFinancialCategoriesFromBlueprintUseCase(
        blueprint_repository, category_repository
    ).execute(company_id="company-1")

    assert [c.name for c in created] == ["Aluguel"]


async def test_raises_not_found_when_no_blueprint_exists() -> None:
    with pytest.raises(NotFoundError):
        await SeedFinancialCategoriesFromBlueprintUseCase(
            FakeCompanyBlueprintRepository(), FakeFinancialCategoryRepository()
        ).execute(company_id="does-not-exist")
