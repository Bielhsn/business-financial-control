from datetime import UTC, datetime

import pytest

from app.application.goals.progress import GetGoalsProgressUseCase, compute_goal_progress
from app.domain.financial.entities import FinancialCategoryType, TransactionStatus
from app.domain.goals.entities import GoalMetric
from tests.fakes import FakeFinancialTransactionRepository, FakeGoalRepository

pytestmark = pytest.mark.anyio


def test_income_goal_uses_income_actual() -> None:
    progress = compute_goal_progress(
        metric=GoalMetric.MONTHLY_INCOME,
        target_cents=100000,
        actual_income=40000,
        actual_net=10000,
        day=10,
        days_in_month=30,
    )
    assert progress.actual_cents == 40000
    assert progress.progress_pct == 40.0
    # Run-rate: 40000 / 10 * 30 = 120000 ≥ 100000 → no caminho.
    assert progress.projected_cents == 120000
    assert progress.on_track is True


def test_net_goal_off_track_when_projection_below_target() -> None:
    progress = compute_goal_progress(
        metric=GoalMetric.MONTHLY_NET,
        target_cents=100000,
        actual_income=0,
        actual_net=20000,
        day=15,
        days_in_month=30,
    )
    # Projeção 40000 < 100000 → fora do caminho.
    assert progress.actual_cents == 20000
    assert progress.projected_cents == 40000
    assert progress.on_track is False


async def test_use_case_returns_empty_without_goals() -> None:
    result = await GetGoalsProgressUseCase(
        FakeGoalRepository(), FakeFinancialTransactionRepository()
    ).execute()
    assert result == []


async def test_use_case_computes_from_current_month_transactions() -> None:
    goals = FakeGoalRepository()
    await goals.set(metric=GoalMetric.MONTHLY_NET, target_cents=100000)
    transactions = FakeFinancialTransactionRepository()

    async def _add(cents: int, when: datetime, kind: FinancialCategoryType) -> None:
        await transactions.create(
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
    await _add(50000, datetime(2026, 7, 3, tzinfo=UTC), FinancialCategoryType.INCOME)
    await _add(10000, datetime(2026, 7, 8, tzinfo=UTC), FinancialCategoryType.EXPENSE)
    # Mês anterior não deve contar.
    await _add(99999, datetime(2026, 6, 30, tzinfo=UTC), FinancialCategoryType.INCOME)

    result = await GetGoalsProgressUseCase(goals, transactions).execute(now=now)

    assert len(result) == 1
    assert result[0].metric == GoalMetric.MONTHLY_NET
    assert result[0].actual_cents == 40000  # 50000 - 10000
