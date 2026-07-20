"""Compõe o panorama do painel administrativo do SaaS.

Puxa listas simples (empresas, assinaturas, conexões, totais financeiros) e faz
toda a matemática (MRR/ARR, churn, segmentação, quebra por plano) em Python puro
— fácil de testar com fakes. Otimizações de agregação no Mongo podem entrar
depois sem mudar esta interface.
"""

from datetime import UTC, datetime

from app.domain.admin.metrics import (
    AdminOverview,
    CompanySummary,
    CustomerMetrics,
    FinancialTotals,
    PlanBreakdown,
    RevenueMetrics,
    SegmentMetric,
    SubscriptionMetrics,
    SystemMetrics,
)
from app.domain.admin.repository import AdminMetricsRepository
from app.domain.subscription.entities import BillingCycle, Subscription, SubscriptionStatus
from app.domain.subscription.plans import PLAN_CATALOG, PlanTier, get_plan
from app.domain.subscription.repository import SubscriptionRepository

_PAYING_STATUSES = frozenset({SubscriptionStatus.ACTIVE})


def monthly_price_cents(subscription: Subscription) -> int:
    """Preço mensal normalizado de uma assinatura (anual dividido por 12)."""
    plan = get_plan(subscription.tier)
    if subscription.billing_cycle == BillingCycle.YEARLY:
        return round(plan.price_cents_yearly / 12)
    return plan.price_cents_monthly


class GetAdminOverviewUseCase:
    def __init__(
        self,
        admin_metrics_repository: AdminMetricsRepository,
        subscription_repository: SubscriptionRepository,
    ) -> None:
        self._admin = admin_metrics_repository
        self._subscriptions = subscription_repository

    async def execute(self, *, now: datetime | None = None) -> AdminOverview:
        moment = now or datetime.now(UTC)
        companies = await self._admin.list_companies()
        subscriptions = await self._subscriptions.list_all()
        connections = await self._admin.list_connections()
        totals = await self._admin.financial_totals()
        user_count = await self._admin.count_users()

        revenue = self._revenue(subscriptions, totals)
        customers = self._customers(companies, subscriptions, moment)
        segments = self._segments(companies)
        subscription_metrics = self._subscriptions_breakdown(subscriptions)
        system = SystemMetrics(
            total_users=user_count,
            total_companies=len(companies),
            total_connections=len(connections),
            connections_with_error=sum(1 for c in connections if c.status == "error"),
        )

        return AdminOverview(
            revenue=revenue,
            customers=customers,
            segments=segments,
            subscriptions=subscription_metrics,
            system=system,
        )

    def _revenue(
        self, subscriptions: list[Subscription], totals: FinancialTotals
    ) -> RevenueMetrics:
        mrr = 0
        active_paying = 0
        trials = 0
        for sub in subscriptions:
            if sub.status == SubscriptionStatus.TRIALING:
                trials += 1
            if sub.status in _PAYING_STATUSES and sub.tier != PlanTier.STARTER:
                mrr += monthly_price_cents(sub)
                active_paying += 1
        return RevenueMetrics(
            mrr_cents=mrr,
            arr_cents=mrr * 12,
            active_paying=active_paying,
            trials=trials,
            platform_gmv_cents=totals.income_cents,
            platform_expenses_cents=totals.expense_cents,
        )

    def _customers(
        self,
        companies: list[CompanySummary],
        subscriptions: list[Subscription],
        moment: datetime,
    ) -> CustomerMetrics:
        total = len(companies)
        active = sum(1 for c in companies if c.is_active)
        new_this_month = sum(
            1
            for c in companies
            if _as_utc(c.created_at).year == moment.year
            and _as_utc(c.created_at).month == moment.month
        )
        churned = sum(1 for s in subscriptions if s.status == SubscriptionStatus.CANCELED)
        paying = sum(
            1 for s in subscriptions if s.status in _PAYING_STATUSES and s.tier != PlanTier.STARTER
        )
        denominator = paying + churned
        churn_rate = round((churned / denominator) * 100, 2) if denominator else 0.0
        return CustomerMetrics(
            total_companies=total,
            active_companies=active,
            inactive_companies=total - active,
            new_this_month=new_this_month,
            churned=churned,
            churn_rate_pct=churn_rate,
        )

    def _segments(self, companies: list[CompanySummary]) -> list[SegmentMetric]:
        counts: dict[str, int] = {}
        for company in companies:
            counts[company.segment] = counts.get(company.segment, 0) + 1
        return [
            SegmentMetric(segment=segment, company_count=count)
            for segment, count in sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
        ]

    def _subscriptions_breakdown(self, subscriptions: list[Subscription]) -> SubscriptionMetrics:
        by_status: dict[SubscriptionStatus, int] = {status: 0 for status in SubscriptionStatus}
        mrr_by_tier: dict[PlanTier, int] = {}
        count_by_tier: dict[PlanTier, int] = {}
        for sub in subscriptions:
            by_status[sub.status] = by_status.get(sub.status, 0) + 1
            count_by_tier[sub.tier] = count_by_tier.get(sub.tier, 0) + 1
            if sub.status in _PAYING_STATUSES and sub.tier != PlanTier.STARTER:
                mrr_by_tier[sub.tier] = mrr_by_tier.get(sub.tier, 0) + monthly_price_cents(sub)
        by_plan = [
            PlanBreakdown(
                tier=plan.tier,
                subscribers=count_by_tier.get(plan.tier, 0),
                mrr_cents=mrr_by_tier.get(plan.tier, 0),
            )
            for plan in PLAN_CATALOG
        ]
        return SubscriptionMetrics(
            by_status=by_status,
            by_plan=by_plan,
            past_due=by_status.get(SubscriptionStatus.PAST_DUE, 0),
        )


def _as_utc(moment: datetime) -> datetime:
    return moment if moment.tzinfo else moment.replace(tzinfo=UTC)
