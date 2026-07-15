from datetime import UTC, datetime, timedelta

import pytest

from app.application.advisor.compute_signals import ComputeBusinessSignalsUseCase, _month_start
from app.application.advisor.recommend import GenerateAdvisorRecommendationsUseCase
from app.application.dashboard.get_dashboard import GetDashboardUseCase
from app.core.exceptions import NotFoundError
from app.domain.advisor.entities import SignalKind, SignalSeverity
from app.domain.catalog.entities import CatalogItemKind
from app.domain.financial.entities import FinancialCategoryType, TransactionStatus
from tests.fakes import (
    FakeAIProvider,
    FakeCatalogItemRepository,
    FakeCompanyBlueprintRepository,
    FakeCompanyRepository,
    FakeFinancialCategoryRepository,
    FakeFinancialTransactionRepository,
)

pytestmark = pytest.mark.anyio


def _use_case(
    items: FakeCatalogItemRepository | None = None,
    transactions: FakeFinancialTransactionRepository | None = None,
) -> ComputeBusinessSignalsUseCase:
    transactions = transactions or FakeFinancialTransactionRepository()
    dashboard = GetDashboardUseCase(
        transactions,
        FakeFinancialCategoryRepository(),
        FakeCompanyBlueprintRepository(),
    )
    return ComputeBusinessSignalsUseCase(
        items or FakeCatalogItemRepository(), transactions, dashboard
    )


async def _add_product(
    repository: FakeCatalogItemRepository,
    *,
    name: str,
    stock: int | None = None,
    tracks: bool = True,
    min_stock: int | None = None,
    price_cents: int = 10000,
    cost_price_cents: int | None = None,
    kind: CatalogItemKind = CatalogItemKind.PRODUCT,
) -> None:
    await repository.create(
        name=name,
        description=None,
        price_cents=price_cents,
        kind=kind,
        tracks_inventory=tracks,
        stock_quantity=stock,
        min_stock=min_stock,
        cost_price_cents=cost_price_cents,
    )


async def test_flags_zero_and_low_stock_products() -> None:
    items = FakeCatalogItemRepository()
    await _add_product(items, name="Camiseta", stock=0)
    await _add_product(items, name="Boné", stock=2, min_stock=5)
    await _add_product(items, name="Meia", stock=50, min_stock=5)
    await _add_product(items, name="Corte", tracks=False, kind=CatalogItemKind.SERVICE)

    signals = await _use_case(items).execute(company_id="company-1")

    kinds = [signal.kind for signal in signals]
    assert kinds.count(SignalKind.STOCK_ZERO) == 1
    assert kinds.count(SignalKind.STOCK_LOW) == 1
    zero = next(signal for signal in signals if signal.kind == SignalKind.STOCK_ZERO)
    assert zero.severity == SignalSeverity.CRITICAL
    assert "Camiseta" in zero.title


async def test_flags_low_margin_items() -> None:
    items = FakeCatalogItemRepository()
    await _add_product(
        items, name="Apertado", tracks=False, price_cents=10000, cost_price_cents=9500
    )
    await _add_product(
        items, name="Saudável", tracks=False, price_cents=10000, cost_price_cents=4000
    )

    signals = await _use_case(items).execute(company_id="company-1")

    low_margin = [signal for signal in signals if signal.kind == SignalKind.LOW_MARGIN]
    assert len(low_margin) == 1
    assert "Apertado" in low_margin[0].title


async def test_flags_revenue_drop_against_previous_months() -> None:
    transactions = FakeFinancialTransactionRepository()
    now = datetime.now(UTC)
    for months_back in (4, 3, 2, 1):
        await transactions.create(
            category_id="c1",
            type=FinancialCategoryType.INCOME,
            amount_cents=100_000,
            description="Vendas",
            status=TransactionStatus.PAID,
            due_date=None,
            paid_at=_month_start(now, months_back) + timedelta(days=3),
            notes=None,
            created_by="user-1",
        )
    await transactions.create(
        category_id="c1",
        type=FinancialCategoryType.INCOME,
        amount_cents=5_000,
        description="Vendas",
        status=TransactionStatus.PAID,
        due_date=None,
        paid_at=_month_start(now, 0) + timedelta(hours=1),
        notes=None,
        created_by="user-1",
    )

    signals = await _use_case(transactions=transactions).execute(company_id="company-1")

    drops = [signal for signal in signals if signal.kind == SignalKind.REVENUE_DROP]
    assert len(drops) == 1
    assert drops[0].severity == SignalSeverity.WARNING


async def test_no_revenue_drop_when_current_month_is_healthy() -> None:
    transactions = FakeFinancialTransactionRepository()
    now = datetime.now(UTC)
    for months_back in (3, 2, 1, 0):
        await transactions.create(
            category_id="c1",
            type=FinancialCategoryType.INCOME,
            amount_cents=100_000,
            description="Vendas",
            status=TransactionStatus.PAID,
            due_date=None,
            paid_at=_month_start(now, months_back) + timedelta(hours=1),
            notes=None,
            created_by="user-1",
        )

    signals = await _use_case(transactions=transactions).execute(company_id="company-1")

    assert not [signal for signal in signals if signal.kind == SignalKind.REVENUE_DROP]


async def test_flags_overdue_pending_transactions() -> None:
    transactions = FakeFinancialTransactionRepository()
    await transactions.create(
        category_id="c1",
        type=FinancialCategoryType.INCOME,
        amount_cents=25_000,
        description="Boleto do cliente",
        status=TransactionStatus.PENDING,
        due_date=datetime.now(UTC) - timedelta(days=3),
        paid_at=None,
        notes=None,
        created_by="user-1",
    )

    signals = await _use_case(transactions=transactions).execute(company_id="company-1")

    overdue = [signal for signal in signals if signal.kind == SignalKind.OVERDUE_BILLS]
    assert len(overdue) == 1
    assert overdue[0].severity == SignalSeverity.CRITICAL


async def test_no_signals_for_empty_company() -> None:
    signals = await _use_case().execute(company_id="company-1")
    assert signals == []


async def test_recommendations_pass_computed_signals_to_ai() -> None:
    companies = FakeCompanyRepository()
    company = await companies.create(
        name="Loja da Ana",
        segment="Loja de roupas",
        employee_count=2,
        average_customer_count=80,
        city="Curitiba",
        state="PR",
        country="Brasil",
        size="Pequena",
        tax_regime=None,
        additional_info=None,
    )
    items = FakeCatalogItemRepository()
    await _add_product(items, name="Camiseta", stock=0)
    transactions = FakeFinancialTransactionRepository()
    dashboard = GetDashboardUseCase(
        transactions, FakeFinancialCategoryRepository(), FakeCompanyBlueprintRepository()
    )
    signals_use_case = ComputeBusinessSignalsUseCase(items, transactions, dashboard)
    ai = FakeAIProvider()

    result = await GenerateAdvisorRecommendationsUseCase(
        companies, signals_use_case, dashboard, ai
    ).execute(company_id=company.id)

    assert "Reponha o estoque" in result.recommendations
    assert len(result.signals) == 1
    assert len(ai.recommendation_calls) == 1
    passed_signals = ai.recommendation_calls[0][2]
    assert passed_signals[0].kind == SignalKind.STOCK_ZERO


async def test_recommendations_raise_not_found_for_unknown_company() -> None:
    transactions = FakeFinancialTransactionRepository()
    dashboard = GetDashboardUseCase(
        transactions, FakeFinancialCategoryRepository(), FakeCompanyBlueprintRepository()
    )
    signals_use_case = ComputeBusinessSignalsUseCase(
        FakeCatalogItemRepository(), transactions, dashboard
    )

    with pytest.raises(NotFoundError):
        await GenerateAdvisorRecommendationsUseCase(
            FakeCompanyRepository(), signals_use_case, dashboard, FakeAIProvider()
        ).execute(company_id="unknown")
