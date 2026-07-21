from datetime import UTC, datetime

import pytest

from app.application.forecast.cashflow import GetCashflowForecastUseCase, compute_forecast
from app.domain.financial.entities import FinancialCategoryType, TransactionStatus
from app.domain.forecast.entities import MonthPoint
from tests.fakes import FakeFinancialTransactionRepository

pytestmark = pytest.mark.anyio


def _month(year: int, month: int, income: int, expense: int) -> MonthPoint:
    return MonthPoint(year=year, month=month, income_cents=income, expense_cents=expense)


def test_current_month_projected_by_run_rate() -> None:
    # Metade do mês (dia 15 de 30) com líquido de 15000 → projeção 30000.
    current = _month(2026, 7, income=15000, expense=0)
    forecast = compute_forecast(history=[], current=current, days_elapsed=15, days_in_month=30)
    assert forecast.current_month_actual_net_cents == 15000
    assert forecast.current_month_projected_net_cents == 30000


def test_next_month_uses_average_of_closed_months() -> None:
    history = [
        _month(2026, 4, 10000, 4000),  # net 6000
        _month(2026, 5, 12000, 4000),  # net 8000
        _month(2026, 6, 16000, 6000),  # net 10000
    ]
    forecast = compute_forecast(
        history=history, current=_month(2026, 7, 0, 0), days_elapsed=1, days_in_month=31
    )
    # Média dos 3 meses fechados: (6000+8000+10000)/3 = 8000.
    assert forecast.next_month_projected_net_cents == 8000


def test_trend_is_positive_when_recent_months_grow() -> None:
    history = [
        _month(2026, 4, 5000, 0),
        _month(2026, 5, 5000, 0),
        _month(2026, 6, 10000, 0),
        _month(2026, 7, 10000, 0),
    ]
    forecast = compute_forecast(
        history=history, current=_month(2026, 8, 0, 0), days_elapsed=1, days_in_month=31
    )
    # Metade antiga média 5000, recente 10000 → +100%.
    assert forecast.trend_pct == 100.0


def test_zero_days_elapsed_projects_actual() -> None:
    forecast = compute_forecast(
        history=[], current=_month(2026, 7, 5000, 0), days_elapsed=0, days_in_month=31
    )
    assert forecast.current_month_projected_net_cents == 5000


async def test_use_case_buckets_transactions_by_month() -> None:
    repo = FakeFinancialTransactionRepository()

    async def _add(cents: int, when: datetime, kind: FinancialCategoryType) -> None:
        await repo.create(
            category_id="c",
            type=kind,
            amount_cents=cents,
            description="x",
            status=TransactionStatus.PAID,
            due_date=None,
            paid_at=when,
            notes=None,
            created_by="u",
        )

    now = datetime(2026, 7, 15, tzinfo=UTC)
    # Mês fechado (junho): receita 10000, despesa 4000 → net 6000.
    await _add(10000, datetime(2026, 6, 10, tzinfo=UTC), FinancialCategoryType.INCOME)
    await _add(4000, datetime(2026, 6, 20, tzinfo=UTC), FinancialCategoryType.EXPENSE)
    # Mês corrente (julho): receita 8000 até o dia 15.
    await _add(8000, datetime(2026, 7, 5, tzinfo=UTC), FinancialCategoryType.INCOME)

    forecast = await GetCashflowForecastUseCase(repo).execute(now=now)

    assert forecast.current_month_actual_net_cents == 8000
    # Run-rate: 8000 / 15 * 31 ≈ 16533.
    assert forecast.current_month_projected_net_cents == round(8000 / 15 * 31)
    june = next(p for p in forecast.history if p.month == 6)
    assert june.net_cents == 6000
