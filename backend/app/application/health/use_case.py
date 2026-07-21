import calendar
from datetime import UTC, datetime

from app.application.forecast.cashflow import GetCashflowForecastUseCase
from app.application.goals.progress import GetGoalsProgressUseCase
from app.application.health.score import compute_health_score
from app.application.platform_sales.analytics import GetSalesAnalyticsUseCase
from app.domain.connector.entities import ConnectionStatus
from app.domain.connector.repository import ConnectionRepository
from app.domain.financial.entities import FinancialCategoryType
from app.domain.financial.repository import FinancialTransactionRepository
from app.domain.goals.repository import GoalRepository
from app.domain.health.entities import HealthScore
from app.domain.platform_sales.repository import PlatformSaleRepository


class GetHealthScoreUseCase:
    """Reúne os sinais e delega o cálculo para compute_health_score."""

    def __init__(
        self,
        *,
        transaction_repository: FinancialTransactionRepository,
        platform_sale_repository: PlatformSaleRepository,
        goal_repository: GoalRepository,
        connection_repository: ConnectionRepository,
    ) -> None:
        self._transactions = transaction_repository
        self._sales = platform_sale_repository
        self._goals = goal_repository
        self._connections = connection_repository

    async def execute(self, *, now: datetime | None = None) -> HealthScore:
        moment = now or datetime.now(UTC)
        month_start = datetime(moment.year, moment.month, 1, tzinfo=UTC)
        month_end = datetime(
            moment.year,
            moment.month,
            calendar.monthrange(moment.year, moment.month)[1],
            23,
            59,
            59,
            tzinfo=UTC,
        )
        month_tx = await self._transactions.list_paid_between(start=month_start, end=month_end)
        income = sum(t.amount_cents for t in month_tx if t.type == FinancialCategoryType.INCOME)
        expense = sum(t.amount_cents for t in month_tx if t.type == FinancialCategoryType.EXPENSE)

        forecast = await GetCashflowForecastUseCase(self._transactions).execute(now=now)
        analytics = await GetSalesAnalyticsUseCase(self._sales).execute(days=30, now=now)
        goals = await GetGoalsProgressUseCase(self._goals, self._transactions).execute(now=now)
        connections = await self._connections.list_all()

        return compute_health_score(
            income_cents=income,
            net_cents=income - expense,
            trend_pct=forecast.trend_pct,
            total_orders=analytics.total_orders,
            total_refunds=analytics.total_refunds,
            goals_total=len(goals),
            goals_on_track=sum(1 for g in goals if g.on_track),
            connections_total=len(connections),
            connections_error=sum(1 for c in connections if c.status == ConnectionStatus.ERROR),
        )
