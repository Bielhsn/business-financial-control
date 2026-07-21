from datetime import datetime

from app.application.alerts.compute import compute_alerts
from app.application.forecast.cashflow import GetCashflowForecastUseCase
from app.application.goals.progress import GetGoalsProgressUseCase
from app.application.platform_sales.analytics import GetSalesAnalyticsUseCase
from app.domain.alerts.entities import Alert
from app.domain.company.repository import CompanyMembershipRepository
from app.domain.connector.entities import ConnectionStatus
from app.domain.connector.repository import ConnectionRepository
from app.domain.financial.repository import FinancialTransactionRepository
from app.domain.goals.repository import GoalRepository
from app.domain.platform_sales.repository import PlatformSaleRepository
from app.domain.subscription.entitlements import resolve_plan
from app.domain.subscription.repository import SubscriptionRepository


class GetAlertsUseCase:
    """Reúne os sinais das outras camadas e delega a decisão para compute_alerts."""

    def __init__(
        self,
        *,
        connection_repository: ConnectionRepository,
        goal_repository: GoalRepository,
        transaction_repository: FinancialTransactionRepository,
        platform_sale_repository: PlatformSaleRepository,
        subscription_repository: SubscriptionRepository,
        membership_repository: CompanyMembershipRepository,
    ) -> None:
        self._connections = connection_repository
        self._goals = goal_repository
        self._transactions = transaction_repository
        self._sales = platform_sale_repository
        self._subscriptions = subscription_repository
        self._memberships = membership_repository

    async def execute(self, *, company_id: str, now: datetime | None = None) -> list[Alert]:
        connections = await self._connections.list_all()
        connections_with_error = sum(1 for c in connections if c.status == ConnectionStatus.ERROR)

        goals_progress = await GetGoalsProgressUseCase(self._goals, self._transactions).execute(
            now=now
        )
        off_track_goals = [
            goal.metric for goal in goals_progress if not goal.on_track and goal.progress_pct < 100
        ]

        forecast = await GetCashflowForecastUseCase(self._transactions).execute(now=now)
        analytics = await GetSalesAnalyticsUseCase(self._sales).execute(days=30, now=now)

        subscription = await self._subscriptions.get_by_company(company_id)
        plan = resolve_plan(subscription)
        members = await self._memberships.list_for_company(company_id)

        return compute_alerts(
            connections_with_error=connections_with_error,
            off_track_goals=off_track_goals,
            projected_net_cents=forecast.current_month_projected_net_cents,
            total_orders=analytics.total_orders,
            total_refunds=analytics.total_refunds,
            members_used=len(members),
            members_limit=plan.limits.max_members,
            integrations_used=len(connections),
            integrations_limit=plan.limits.max_integrations,
        )
