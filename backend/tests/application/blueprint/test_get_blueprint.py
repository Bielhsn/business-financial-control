import pytest

from app.application.blueprint.get_blueprint import GetCompanyBlueprintUseCase
from app.core.exceptions import NotFoundError
from app.domain.blueprint.entities import KPIDefinition, SuggestedFinancialCategory
from app.domain.financial.entities import FinancialCategoryType
from tests.fakes import FakeCompanyBlueprintRepository

pytestmark = pytest.mark.anyio


async def test_returns_the_existing_blueprint() -> None:
    repository = FakeCompanyBlueprintRepository()
    await repository.upsert(
        company_id="company-1",
        modules=["financial_core"],
        financial_categories=[
            SuggestedFinancialCategory(name="Vendas", type=FinancialCategoryType.INCOME)
        ],
        kpis=[KPIDefinition(key="x", name="X", description="Y")],
        client_custom_fields=[],
        ai_provider="anthropic",
    )

    result = await GetCompanyBlueprintUseCase(repository).execute(company_id="company-1")

    assert result.company_id == "company-1"


async def test_raises_not_found_when_no_blueprint_exists() -> None:
    with pytest.raises(NotFoundError):
        await GetCompanyBlueprintUseCase(FakeCompanyBlueprintRepository()).execute(
            company_id="company-1"
        )
