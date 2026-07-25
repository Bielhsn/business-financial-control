from datetime import UTC, datetime

import pytest

from app.application.admin.overview import GetAdminOverviewUseCase
from app.application.subscription.change_plan import ChangePlanUseCase
from app.domain.admin.metrics import CompanySummary, ConnectionSummary
from app.domain.subscription.entities import BillingCycle, SubscriptionStatus
from app.domain.subscription.plans import PlanTier, get_plan
from tests.fakes import FakeAdminMetricsRepository, FakeSubscriptionRepository

pytestmark = pytest.mark.anyio


def _company(cid: str, segment: str, *, active: bool = True, created: datetime | None = None):
    return CompanySummary(
        id=cid,
        name=f"Empresa {cid}",
        segment=segment,
        is_active=active,
        created_at=created or datetime(2026, 7, 1, tzinfo=UTC),
    )


async def _overview(admin: FakeAdminMetricsRepository, subs: FakeSubscriptionRepository):
    return await GetAdminOverviewUseCase(admin, subs).execute(now=datetime(2026, 7, 20, tzinfo=UTC))


async def test_mrr_sums_active_paid_subscriptions() -> None:
    admin = FakeAdminMetricsRepository()
    subs = FakeSubscriptionRepository()
    await ChangePlanUseCase(subs).execute(company_id="c1", tier=PlanTier.PROFESSIONAL)
    await ChangePlanUseCase(subs).execute(company_id="c2", tier=PlanTier.BUSINESS)

    overview = await _overview(admin, subs)

    expected = (
        get_plan(PlanTier.PROFESSIONAL).price_cents_monthly
        + get_plan(PlanTier.BUSINESS).price_cents_monthly
    )
    assert overview.revenue.mrr_cents == expected
    assert overview.revenue.arr_cents == expected * 12
    assert overview.revenue.active_paying == 2


async def test_starter_and_trial_do_not_count_as_mrr() -> None:
    admin = FakeAdminMetricsRepository()
    subs = FakeSubscriptionRepository()
    await ChangePlanUseCase(subs).execute(company_id="c1", tier=PlanTier.STARTER)
    await ChangePlanUseCase(subs).execute(
        company_id="c2", tier=PlanTier.PROFESSIONAL, start_trial=True
    )

    overview = await _overview(admin, subs)

    assert overview.revenue.mrr_cents == 0
    assert overview.revenue.trials == 1
    assert overview.revenue.active_paying == 0


async def test_yearly_billing_is_normalized_to_monthly() -> None:
    admin = FakeAdminMetricsRepository()
    subs = FakeSubscriptionRepository()
    await ChangePlanUseCase(subs).execute(
        company_id="c1", tier=PlanTier.PROFESSIONAL, billing_cycle=BillingCycle.YEARLY
    )

    overview = await _overview(admin, subs)

    expected = round(get_plan(PlanTier.PROFESSIONAL).price_cents_yearly / 12)
    assert overview.revenue.mrr_cents == expected


async def test_churn_rate_and_customers() -> None:
    admin = FakeAdminMetricsRepository()
    admin.companies = [
        _company("c1", "Barbearia"),
        _company("c2", "Barbearia", active=False),
        _company("c3", "Restaurante", created=datetime(2026, 7, 15, tzinfo=UTC)),
    ]
    admin.users = 5
    subs = FakeSubscriptionRepository()
    await ChangePlanUseCase(subs).execute(company_id="c1", tier=PlanTier.PROFESSIONAL)
    # c2 cancelou
    from app.application.subscription.change_plan import CancelSubscriptionUseCase

    await ChangePlanUseCase(subs).execute(company_id="c2", tier=PlanTier.BUSINESS)
    await CancelSubscriptionUseCase(subs).execute(company_id="c2")

    overview = await _overview(admin, subs)

    assert overview.customers.total_companies == 3
    assert overview.customers.active_companies == 2
    assert overview.customers.inactive_companies == 1
    assert overview.customers.new_this_month == 3  # todas criadas em julho/2026
    assert overview.customers.churned == 1
    # 1 pagante ativo + 1 cancelado => churn 50%
    assert overview.customers.churn_rate_pct == 50.0


async def test_segments_are_counted_and_sorted() -> None:
    admin = FakeAdminMetricsRepository()
    admin.companies = [
        _company("c1", "Barbearia"),
        _company("c2", "Barbearia"),
        _company("c3", "Restaurante"),
    ]
    overview = await _overview(admin, FakeSubscriptionRepository())
    assert overview.segments[0].segment == "Barbearia"
    assert overview.segments[0].company_count == 2


async def test_system_metrics_and_connection_errors() -> None:
    admin = FakeAdminMetricsRepository()
    admin.users = 12
    admin.companies = [_company("c1", "Loja")]
    admin.connections = [
        ConnectionSummary(provider="hotmart", status="connected"),
        ConnectionSummary(provider="shopify", status="error"),
    ]
    admin.income_cents = 100_000
    admin.expense_cents = 30_000

    overview = await _overview(admin, FakeSubscriptionRepository())

    assert overview.system is not None
    assert overview.system.total_users == 12
    assert overview.system.total_connections == 2
    assert overview.system.connections_with_error == 1
    assert overview.revenue.platform_gmv_cents == 100_000
    assert overview.revenue.platform_expenses_cents == 30_000


async def test_subscriptions_breakdown_by_plan() -> None:
    admin = FakeAdminMetricsRepository()
    subs = FakeSubscriptionRepository()
    await ChangePlanUseCase(subs).execute(company_id="c1", tier=PlanTier.PROFESSIONAL)
    await ChangePlanUseCase(subs).execute(company_id="c2", tier=PlanTier.PROFESSIONAL)

    overview = await _overview(admin, subs)
    assert overview.subscriptions is not None
    pro = next(b for b in overview.subscriptions.by_plan if b.tier == PlanTier.PROFESSIONAL)
    assert pro.subscribers == 2
    assert overview.subscriptions.by_status[SubscriptionStatus.ACTIVE] == 2
