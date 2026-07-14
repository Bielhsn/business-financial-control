import pytest

from app.application.company.create_company import CreateCompanyUseCase
from app.domain.company.roles import CompanyRole
from tests.fakes import FakeCompanyMembershipRepository, FakeCompanyRepository

pytestmark = pytest.mark.anyio


def _payload(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "owner_id": "user-1",
        "name": "  Barbearia do Zé  ",
        "segment": "Barbearia",
        "employee_count": 3,
        "average_customer_count": 120,
        "city": "São Paulo",
        "state": "SP",
        "country": "Brasil",
        "size": "Pequena",
        "tax_regime": "Simples Nacional",
        "additional_info": None,
    }
    base.update(overrides)
    return base


async def test_creates_company_and_membership_as_owner() -> None:
    company_repository = FakeCompanyRepository()
    membership_repository = FakeCompanyMembershipRepository()
    use_case = CreateCompanyUseCase(company_repository, membership_repository)

    company = await use_case.execute(**_payload())

    assert company.name == "Barbearia do Zé"
    membership = await membership_repository.get_by_user_and_company("user-1", company.id)
    assert membership is not None
    assert membership.role == CompanyRole.OWNER


async def test_rolls_back_company_when_membership_creation_fails() -> None:
    company_repository = FakeCompanyRepository()
    membership_repository = FakeCompanyMembershipRepository()
    membership_repository.fail_on_create = True
    use_case = CreateCompanyUseCase(company_repository, membership_repository)

    with pytest.raises(RuntimeError):
        await use_case.execute(**_payload())

    assert len(company_repository._companies) == 0
