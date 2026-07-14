import pytest

from app.application.company.create_company import CreateCompanyUseCase
from app.application.company.update_company import UpdateCompanyUseCase
from app.core.exceptions import NotFoundError
from tests.fakes import FakeCompanyMembershipRepository, FakeCompanyRepository

pytestmark = pytest.mark.anyio


async def _create_company(company_repository: FakeCompanyRepository) -> str:
    use_case = CreateCompanyUseCase(company_repository, FakeCompanyMembershipRepository())
    company = await use_case.execute(
        owner_id="user-1",
        name="Empresa A",
        segment="Tecnologia",
        employee_count=5,
        average_customer_count=10,
        city="Curitiba",
        state="PR",
        country="Brasil",
        size="Pequena",
        tax_regime=None,
        additional_info=None,
    )
    return company.id


async def test_updates_only_the_provided_fields() -> None:
    company_repository = FakeCompanyRepository()
    company_id = await _create_company(company_repository)

    updated = await UpdateCompanyUseCase(company_repository).execute(
        company_id=company_id, name="Empresa A Renomeada"
    )

    assert updated.name == "Empresa A Renomeada"
    assert updated.segment == "Tecnologia"


async def test_raises_not_found_for_unknown_company() -> None:
    company_repository = FakeCompanyRepository()

    with pytest.raises(NotFoundError):
        await UpdateCompanyUseCase(company_repository).execute(
            company_id="does-not-exist", name="Novo nome"
        )


async def test_returns_company_unchanged_when_no_fields_are_provided() -> None:
    company_repository = FakeCompanyRepository()
    company_id = await _create_company(company_repository)

    result = await UpdateCompanyUseCase(company_repository).execute(company_id=company_id)

    assert result.name == "Empresa A"


async def test_raises_not_found_when_no_fields_are_provided_for_unknown_company() -> None:
    company_repository = FakeCompanyRepository()

    with pytest.raises(NotFoundError):
        await UpdateCompanyUseCase(company_repository).execute(company_id="does-not-exist")
