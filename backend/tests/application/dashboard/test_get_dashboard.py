from datetime import UTC, datetime

import pytest

from app.application.dashboard.get_dashboard import GetDashboardUseCase
from app.core.exceptions import ValidationError
from app.domain.blueprint.entities import KPIDefinition
from app.domain.dashboard.kpi_registry import KPIMetric, KPIUnit
from app.domain.financial.entities import FinancialCategoryType, TransactionStatus
from tests.fakes import (
    FakeCompanyBlueprintRepository,
    FakeFinancialCategoryRepository,
    FakeFinancialTransactionRepository,
)

pytestmark = pytest.mark.anyio


def _build_use_case(
    transaction_repository: FakeFinancialTransactionRepository | None = None,
    category_repository: FakeFinancialCategoryRepository | None = None,
    blueprint_repository: FakeCompanyBlueprintRepository | None = None,
) -> GetDashboardUseCase:
    return GetDashboardUseCase(
        transaction_repository or FakeFinancialTransactionRepository(),
        category_repository or FakeFinancialCategoryRepository(),
        blueprint_repository or FakeCompanyBlueprintRepository(),
    )


async def test_computes_revenue_expense_profit_and_margin_for_the_period() -> None:
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
    await transactions.create(
        category_id="c2",
        type=FinancialCategoryType.EXPENSE,
        amount_cents=4000,
        description="Aluguel",
        status=TransactionStatus.PAID,
        due_date=None,
        paid_at=datetime(2026, 6, 20, tzinfo=UTC),
        notes=None,
        created_by="user-1",
    )
    # fora do período: não deve contar
    await transactions.create(
        category_id="c1",
        type=FinancialCategoryType.INCOME,
        amount_cents=5000,
        description="Venda anterior",
        status=TransactionStatus.PAID,
        due_date=None,
        paid_at=datetime(2026, 5, 15, tzinfo=UTC),
        notes=None,
        created_by="user-1",
    )

    summary = await _build_use_case(transaction_repository=transactions).execute(
        company_id="company-1",
        start=datetime(2026, 6, 1, tzinfo=UTC),
        end=datetime(2026, 6, 30, 23, 59, 59, tzinfo=UTC),
        months=1,
    )

    assert summary.revenue_cents == 10000
    assert summary.expense_cents == 4000
    assert summary.profit_cents == 6000
    assert summary.profit_margin_pct == 60.0


async def test_profit_margin_is_none_when_there_is_no_revenue() -> None:
    summary = await _build_use_case().execute(
        company_id="company-1",
        start=datetime(2026, 6, 1, tzinfo=UTC),
        end=datetime(2026, 6, 30, tzinfo=UTC),
    )

    assert summary.profit_margin_pct is None
    assert summary.average_ticket_cents == 0


async def test_computes_average_ticket_and_transaction_count() -> None:
    transactions = FakeFinancialTransactionRepository()
    for amount in (10000, 20000):
        await transactions.create(
            category_id="c1",
            type=FinancialCategoryType.INCOME,
            amount_cents=amount,
            description="Venda",
            status=TransactionStatus.PAID,
            due_date=None,
            paid_at=datetime(2026, 6, 10, tzinfo=UTC),
            notes=None,
            created_by="user-1",
        )
    await transactions.create(
        category_id="c2",
        type=FinancialCategoryType.EXPENSE,
        amount_cents=3000,
        description="Compra",
        status=TransactionStatus.PAID,
        due_date=None,
        paid_at=datetime(2026, 6, 12, tzinfo=UTC),
        notes=None,
        created_by="user-1",
    )

    summary = await _build_use_case(transaction_repository=transactions).execute(
        company_id="company-1",
        start=datetime(2026, 6, 1, tzinfo=UTC),
        end=datetime(2026, 6, 30, tzinfo=UTC),
    )

    assert summary.average_ticket_cents == 15000
    assert summary.transaction_count == 3


async def test_active_clients_counts_distinct_clients_with_paid_transactions() -> None:
    transactions = FakeFinancialTransactionRepository()
    for client_id in ("client-1", "client-1", "client-2", None):
        await transactions.create(
            category_id="c1",
            type=FinancialCategoryType.INCOME,
            amount_cents=1000,
            description="Venda",
            status=TransactionStatus.PAID,
            due_date=None,
            paid_at=datetime(2026, 6, 10, tzinfo=UTC),
            notes=None,
            client_id=client_id,
            created_by="user-1",
        )

    summary = await _build_use_case(transaction_repository=transactions).execute(
        company_id="company-1",
        start=datetime(2026, 6, 1, tzinfo=UTC),
        end=datetime(2026, 6, 30, tzinfo=UTC),
    )

    assert summary.active_clients == 2


async def test_builds_monthly_breakdown_across_the_requested_window() -> None:
    transactions = FakeFinancialTransactionRepository()
    await transactions.create(
        category_id="c1",
        type=FinancialCategoryType.INCOME,
        amount_cents=1000,
        description="Abril",
        status=TransactionStatus.PAID,
        due_date=None,
        paid_at=datetime(2026, 4, 10, tzinfo=UTC),
        notes=None,
        created_by="user-1",
    )
    await transactions.create(
        category_id="c1",
        type=FinancialCategoryType.INCOME,
        amount_cents=2000,
        description="Maio",
        status=TransactionStatus.PAID,
        due_date=None,
        paid_at=datetime(2026, 5, 10, tzinfo=UTC),
        notes=None,
        created_by="user-1",
    )
    await transactions.create(
        category_id="c2",
        type=FinancialCategoryType.EXPENSE,
        amount_cents=500,
        description="Junho",
        status=TransactionStatus.PAID,
        due_date=None,
        paid_at=datetime(2026, 6, 10, tzinfo=UTC),
        notes=None,
        created_by="user-1",
    )

    summary = await _build_use_case(transaction_repository=transactions).execute(
        company_id="company-1",
        start=datetime(2026, 6, 1, tzinfo=UTC),
        end=datetime(2026, 6, 30, tzinfo=UTC),
        months=3,
    )

    assert [(b.year, b.month) for b in summary.monthly_breakdown] == [
        (2026, 4),
        (2026, 5),
        (2026, 6),
    ]
    assert summary.monthly_breakdown[0].revenue_cents == 1000
    assert summary.monthly_breakdown[1].revenue_cents == 2000
    assert summary.monthly_breakdown[2].expense_cents == 500
    assert summary.monthly_breakdown[2].profit_cents == -500


async def test_top_categories_are_ordered_descending_and_limited_to_five() -> None:
    transactions = FakeFinancialTransactionRepository()
    categories = FakeFinancialCategoryRepository()
    amounts = [6000, 5000, 4000, 3000, 2000, 1000]
    category_ids = []
    for index, amount in enumerate(amounts):
        category = await categories.create(
            name=f"Categoria {index}", type=FinancialCategoryType.INCOME
        )
        category_ids.append(category.id)
        await transactions.create(
            category_id=category.id,
            type=FinancialCategoryType.INCOME,
            amount_cents=amount,
            description="Venda",
            status=TransactionStatus.PAID,
            due_date=None,
            paid_at=datetime(2026, 6, 10, tzinfo=UTC),
            notes=None,
            created_by="user-1",
        )

    summary = await _build_use_case(
        transaction_repository=transactions, category_repository=categories
    ).execute(
        company_id="company-1",
        start=datetime(2026, 6, 1, tzinfo=UTC),
        end=datetime(2026, 6, 30, tzinfo=UTC),
    )

    assert len(summary.top_income_categories) == 5
    assert [c.total_cents for c in summary.top_income_categories] == [6000, 5000, 4000, 3000, 2000]
    assert summary.top_income_categories[0].category_name == "Categoria 0"


async def test_period_comparison_computes_percentage_change() -> None:
    transactions = FakeFinancialTransactionRepository()
    await transactions.create(
        category_id="c1",
        type=FinancialCategoryType.INCOME,
        amount_cents=5000,
        description="Mês anterior",
        status=TransactionStatus.PAID,
        due_date=None,
        paid_at=datetime(2026, 5, 15, tzinfo=UTC),
        notes=None,
        created_by="user-1",
    )
    await transactions.create(
        category_id="c1",
        type=FinancialCategoryType.INCOME,
        amount_cents=10000,
        description="Mês atual",
        status=TransactionStatus.PAID,
        due_date=None,
        paid_at=datetime(2026, 6, 15, tzinfo=UTC),
        notes=None,
        created_by="user-1",
    )

    summary = await _build_use_case(transaction_repository=transactions).execute(
        company_id="company-1",
        start=datetime(2026, 6, 1, tzinfo=UTC),
        end=datetime(2026, 6, 30, tzinfo=UTC),
    )

    assert summary.comparison.revenue_change_pct == 100.0


async def test_period_comparison_is_none_when_previous_period_had_no_value() -> None:
    summary = await _build_use_case().execute(
        company_id="company-1",
        start=datetime(2026, 6, 1, tzinfo=UTC),
        end=datetime(2026, 6, 30, tzinfo=UTC),
    )

    assert summary.comparison.revenue_change_pct is None
    assert summary.comparison.expense_change_pct is None
    assert summary.comparison.profit_change_pct is None


async def test_kpis_are_resolved_against_the_company_blueprint() -> None:
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
    blueprint_repository = FakeCompanyBlueprintRepository()
    await blueprint_repository.upsert(
        company_id="company-1",
        modules=["financial_core"],
        financial_categories=[],
        kpis=[
            KPIDefinition(
                key="total_revenue",
                name="Receita total",
                description="Receita do período.",
                metric=KPIMetric.TOTAL_REVENUE,
            )
        ],
        client_custom_fields=[],
        ai_provider="anthropic",
    )

    summary = await _build_use_case(
        transaction_repository=transactions, blueprint_repository=blueprint_repository
    ).execute(
        company_id="company-1",
        start=datetime(2026, 6, 1, tzinfo=UTC),
        end=datetime(2026, 6, 30, tzinfo=UTC),
    )

    assert len(summary.kpis) == 1
    assert summary.kpis[0].metric == KPIMetric.TOTAL_REVENUE
    assert summary.kpis[0].unit == KPIUnit.CENTS
    assert summary.kpis[0].value == 10000.0


async def test_kpis_is_empty_when_no_blueprint_exists() -> None:
    summary = await _build_use_case().execute(
        company_id="company-1",
        start=datetime(2026, 6, 1, tzinfo=UTC),
        end=datetime(2026, 6, 30, tzinfo=UTC),
    )

    assert summary.kpis == []


async def test_raises_validation_error_when_end_is_not_after_start() -> None:
    with pytest.raises(ValidationError):
        await _build_use_case().execute(
            company_id="company-1",
            start=datetime(2026, 6, 30, tzinfo=UTC),
            end=datetime(2026, 6, 1, tzinfo=UTC),
        )


async def test_raises_validation_error_when_months_is_less_than_one() -> None:
    with pytest.raises(ValidationError):
        await _build_use_case().execute(
            company_id="company-1",
            start=datetime(2026, 6, 1, tzinfo=UTC),
            end=datetime(2026, 6, 30, tzinfo=UTC),
            months=0,
        )
