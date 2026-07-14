import pytest

from app.application.company.create_company import CreateCompanyUseCase
from app.application.company.list_my_companies import ListMyCompaniesUseCase
from app.domain.company.roles import CompanyRole
from tests.fakes import FakeCompanyMembershipRepository, FakeCompanyRepository

pytestmark = pytest.mark.anyio


async def test_lists_only_companies_the_user_belongs_to() -> None:
    company_repository = FakeCompanyRepository()
    membership_repository = FakeCompanyMembershipRepository()
    create_use_case = CreateCompanyUseCase(company_repository, membership_repository)

    await create_use_case.execute(
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
    await create_use_case.execute(
        owner_id="user-2",
        name="Empresa B",
        segment="Restaurante",
        employee_count=8,
        average_customer_count=200,
        city="Curitiba",
        state="PR",
        country="Brasil",
        size="Média",
        tax_regime=None,
        additional_info=None,
    )

    use_case = ListMyCompaniesUseCase(membership_repository, company_repository)
    results = await use_case.execute(user_id="user-1")

    assert len(results) == 1
    assert results[0].company.name == "Empresa A"
    assert results[0].role == CompanyRole.OWNER
