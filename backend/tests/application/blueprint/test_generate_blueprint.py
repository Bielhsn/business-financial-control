import pytest

from app.application.blueprint.generate_blueprint import GenerateCompanyBlueprintUseCase
from app.core.exceptions import NotFoundError
from tests.fakes import FakeAIProvider, FakeCompanyBlueprintRepository, FakeCompanyRepository

pytestmark = pytest.mark.anyio


async def _create_company(company_repository: FakeCompanyRepository) -> str:
    company = await company_repository.create(
        name="Barbearia do Zé",
        segment="Barbearia",
        employee_count=3,
        average_customer_count=100,
        city="São Paulo",
        state="SP",
        country="Brasil",
        size="Pequena",
        tax_regime=None,
        additional_info=None,
    )
    return company.id


async def test_generates_and_persists_a_blueprint() -> None:
    company_repository = FakeCompanyRepository()
    company_id = await _create_company(company_repository)
    blueprint_repository = FakeCompanyBlueprintRepository()
    ai_provider = FakeAIProvider()

    use_case = GenerateCompanyBlueprintUseCase(
        company_repository, blueprint_repository, ai_provider, "anthropic"
    )
    blueprint = await use_case.execute(
        company_id=company_id, additional_context="Atende com hora marcada."
    )

    assert blueprint.company_id == company_id
    assert blueprint.ai_provider == "anthropic"
    assert blueprint.modules == ["financial_core", "clients"]
    assert len(ai_provider.calls) == 1
    called_company, called_context = ai_provider.calls[0]
    assert called_company.id == company_id
    assert called_context == "Atende com hora marcada."


async def test_raises_not_found_for_unknown_company() -> None:
    use_case = GenerateCompanyBlueprintUseCase(
        FakeCompanyRepository(), FakeCompanyBlueprintRepository(), FakeAIProvider(), "anthropic"
    )

    with pytest.raises(NotFoundError):
        await use_case.execute(company_id="does-not-exist", additional_context=None)


async def test_regenerating_replaces_the_existing_blueprint_in_place() -> None:
    company_repository = FakeCompanyRepository()
    company_id = await _create_company(company_repository)
    blueprint_repository = FakeCompanyBlueprintRepository()
    ai_provider = FakeAIProvider()
    use_case = GenerateCompanyBlueprintUseCase(
        company_repository, blueprint_repository, ai_provider, "anthropic"
    )

    first = await use_case.execute(company_id=company_id, additional_context=None)
    second = await use_case.execute(company_id=company_id, additional_context=None)

    assert first.id == second.id
    assert len(ai_provider.calls) == 2
