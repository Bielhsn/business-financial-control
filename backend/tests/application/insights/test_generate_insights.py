from datetime import UTC, datetime

import pytest

from app.application.dashboard.get_dashboard import GetDashboardUseCase
from app.application.insights.generate_insights import GenerateFinancialInsightsUseCase
from app.core.exceptions import NotFoundError
from app.domain.financial.entities import FinancialCategoryType, TransactionStatus
from app.domain.insights.entities import InsightKind
from tests.fakes import (
    FakeAIProvider,
    FakeCompanyBlueprintRepository,
    FakeCompanyRepository,
    FakeFinancialCategoryRepository,
    FakeFinancialTransactionRepository,
)

pytestmark = pytest.mark.anyio


def _dashboard_use_case(
    transactions: FakeFinancialTransactionRepository | None = None,
) -> GetDashboardUseCase:
    return GetDashboardUseCase(
        transactions or FakeFinancialTransactionRepository(),
        FakeFinancialCategoryRepository(),
        FakeCompanyBlueprintRepository(),
    )


async def _create_company(repository: FakeCompanyRepository) -> str:
    company = await repository.create(
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


async def test_composes_dashboard_summary_and_ai_insights() -> None:
    companies = FakeCompanyRepository()
    company_id = await _create_company(companies)
    transactions = FakeFinancialTransactionRepository()
    await transactions.create(
        category_id="c1",
        type=FinancialCategoryType.INCOME,
        amount_cents=10000,
        description="Venda",
        status=TransactionStatus.PAID,
        due_date=None,
        paid_at=datetime(2026, 6, 15, tzinfo=UTC),
        notes=None,
        created_by="user-1",
    )
    ai = FakeAIProvider()

    result = await GenerateFinancialInsightsUseCase(
        companies, _dashboard_use_case(transactions), ai
    ).execute(
        company_id=company_id,
        start=datetime(2026, 6, 1, tzinfo=UTC),
        end=datetime(2026, 6, 30, tzinfo=UTC),
    )

    assert result.summary.revenue_cents == 10000
    assert len(result.insights) == 2
    assert result.insights[0].kind == InsightKind.HIGHLIGHT
    # A IA recebeu exatamente o resumo computado pela aplicação.
    assert len(ai.insight_calls) == 1
    assert ai.insight_calls[0][1].revenue_cents == 10000


async def test_raises_not_found_for_unknown_company() -> None:
    with pytest.raises(NotFoundError):
        await GenerateFinancialInsightsUseCase(
            FakeCompanyRepository(), _dashboard_use_case(), FakeAIProvider()
        ).execute(
            company_id="unknown",
            start=datetime(2026, 6, 1, tzinfo=UTC),
            end=datetime(2026, 6, 30, tzinfo=UTC),
        )
