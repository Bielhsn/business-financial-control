"""Acompanhamento de metas: realizado no mês corrente × meta × projeção por
run-rate (mesmo método do forecast, mantendo a leitura consistente)."""

import calendar
from dataclasses import dataclass
from datetime import UTC, datetime

from app.domain.financial.entities import FinancialCategoryType
from app.domain.financial.repository import FinancialTransactionRepository
from app.domain.goals.entities import GoalMetric
from app.domain.goals.repository import GoalRepository


@dataclass(frozen=True)
class GoalProgress:
    metric: GoalMetric
    target_cents: int
    actual_cents: int
    projected_cents: int
    progress_pct: float  # realizado / meta * 100 (0..∞)
    on_track: bool  # a projeção alcança a meta?


def _run_rate(actual: int, day: int, days_in_month: int) -> int:
    if day <= 0:
        return actual
    return round(actual / day * days_in_month)


def compute_goal_progress(
    *,
    metric: GoalMetric,
    target_cents: int,
    actual_income: int,
    actual_net: int,
    day: int,
    days_in_month: int,
) -> GoalProgress:
    actual = actual_income if metric == GoalMetric.MONTHLY_INCOME else actual_net
    projected = _run_rate(actual, day, days_in_month)
    progress = round((actual / target_cents) * 100, 2) if target_cents > 0 else 0.0
    return GoalProgress(
        metric=metric,
        target_cents=target_cents,
        actual_cents=actual,
        projected_cents=projected,
        progress_pct=progress,
        on_track=projected >= target_cents,
    )


class GetGoalsProgressUseCase:
    def __init__(
        self,
        goal_repository: GoalRepository,
        transaction_repository: FinancialTransactionRepository,
    ) -> None:
        self._goals = goal_repository
        self._transactions = transaction_repository

    async def execute(self, *, now: datetime | None = None) -> list[GoalProgress]:
        goals = await self._goals.list_all()
        if not goals:
            return []

        moment = now or datetime.now(UTC)
        month_start = datetime(moment.year, moment.month, 1, tzinfo=UTC)
        transactions = await self._transactions.list_paid_between(start=month_start, end=moment)
        actual_income = sum(
            t.amount_cents for t in transactions if t.type == FinancialCategoryType.INCOME
        )
        actual_expense = sum(
            t.amount_cents for t in transactions if t.type == FinancialCategoryType.EXPENSE
        )
        actual_net = actual_income - actual_expense
        days_in_month = calendar.monthrange(moment.year, moment.month)[1]

        return [
            compute_goal_progress(
                metric=goal.metric,
                target_cents=goal.target_cents,
                actual_income=actual_income,
                actual_net=actual_net,
                day=moment.day,
                days_in_month=days_in_month,
            )
            for goal in goals
        ]
