from datetime import UTC, datetime

import pytest

from app.application.maintenance.run_scheduled import RunScheduledMaintenanceUseCase
from app.core.tenant import set_current_company_id
from app.domain.financial.entities import FinancialCategoryType
from app.domain.recurring.entities import RecurrenceFrequency
from tests.fakes import (
    FakeCompanyRepository,
    FakeFinancialTransactionRepository,
    FakeRecurringTransactionRepository,
)

pytestmark = pytest.mark.anyio

_COMPANY = {
    "segment": "Serviços",
    "employee_count": 1,
    "average_customer_count": 1,
    "city": "SP",
    "state": "SP",
    "country": "BR",
    "size": "Pequena",
    "tax_regime": None,
    "additional_info": None,
}


async def _seed_company(companies: FakeCompanyRepository, name: str) -> str:
    company = await companies.create(name=name, **_COMPANY)
    return company.id


async def _seed_recurring(
    recurring: FakeRecurringTransactionRepository, company_id: str, description: str
) -> None:
    set_current_company_id(company_id)
    await recurring.create(
        category_id="cat",
        type=FinancialCategoryType.EXPENSE,
        amount_cents=100000,
        description=description,
        frequency=RecurrenceFrequency.MONTHLY,
        anchor_day=5,
        next_run_date=datetime(2026, 7, 5, tzinfo=UTC),
        notes=None,
        client_id=None,
        created_by="owner",
    )


async def test_runs_generation_for_every_company_isolated() -> None:
    companies = FakeCompanyRepository()
    recurring = FakeRecurringTransactionRepository()
    transactions = FakeFinancialTransactionRepository()

    company_a = await _seed_company(companies, "A")
    company_b = await _seed_company(companies, "B")
    await _seed_recurring(recurring, company_a, "Aluguel A")
    await _seed_recurring(recurring, company_b, "Aluguel B")

    result = await RunScheduledMaintenanceUseCase(companies, recurring, transactions).execute(
        as_of=datetime(2026, 7, 20, tzinfo=UTC)
    )

    # Cada empresa gerou exatamente 1 lançamento (isolamento por tenant).
    assert result.companies == 2
    assert result.recurring_created == 2
    assert result.per_company == {company_a: 1, company_b: 1}
    assert len(await transactions.list_all()) == 2


async def test_is_idempotent_across_runs() -> None:
    companies = FakeCompanyRepository()
    recurring = FakeRecurringTransactionRepository()
    transactions = FakeFinancialTransactionRepository()
    company_id = await _seed_company(companies, "A")
    await _seed_recurring(recurring, company_id, "Aluguel")
    use_case = RunScheduledMaintenanceUseCase(companies, recurring, transactions)

    first = await use_case.execute(as_of=datetime(2026, 7, 6, tzinfo=UTC))
    second = await use_case.execute(as_of=datetime(2026, 7, 6, tzinfo=UTC))

    assert first.recurring_created == 1
    assert second.recurring_created == 0
    assert len(await transactions.list_all()) == 1


async def test_no_companies_is_a_noop() -> None:
    result = await RunScheduledMaintenanceUseCase(
        FakeCompanyRepository(),
        FakeRecurringTransactionRepository(),
        FakeFinancialTransactionRepository(),
    ).execute(as_of=datetime(2026, 7, 20, tzinfo=UTC))

    assert result.companies == 0
    assert result.recurring_created == 0
