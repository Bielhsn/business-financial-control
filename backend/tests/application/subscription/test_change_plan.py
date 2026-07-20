import pytest

from app.application.subscription.change_plan import (
    CancelSubscriptionUseCase,
    ChangePlanUseCase,
)
from app.domain.subscription.entities import BillingCycle, SubscriptionStatus
from app.domain.subscription.plans import PlanTier
from tests.fakes import FakeSubscriptionRepository

pytestmark = pytest.mark.anyio


async def test_change_to_paid_plan_activates_with_period() -> None:
    repo = FakeSubscriptionRepository()
    use_case = ChangePlanUseCase(repo)

    sub = await use_case.execute(company_id="c1", tier=PlanTier.PROFESSIONAL)

    assert sub.tier == PlanTier.PROFESSIONAL
    assert sub.status == SubscriptionStatus.ACTIVE
    assert sub.current_period_end is not None
    assert sub.trial_ends_at is None


async def test_start_trial_sets_trialing_status() -> None:
    repo = FakeSubscriptionRepository()
    sub = await ChangePlanUseCase(repo).execute(
        company_id="c1", tier=PlanTier.BUSINESS, start_trial=True
    )
    assert sub.status == SubscriptionStatus.TRIALING
    assert sub.trial_ends_at is not None


async def test_starter_never_has_trial_or_period() -> None:
    repo = FakeSubscriptionRepository()
    sub = await ChangePlanUseCase(repo).execute(
        company_id="c1", tier=PlanTier.STARTER, start_trial=True
    )
    assert sub.status == SubscriptionStatus.ACTIVE
    assert sub.trial_ends_at is None
    assert sub.current_period_end is None


async def test_yearly_cycle_is_persisted() -> None:
    repo = FakeSubscriptionRepository()
    sub = await ChangePlanUseCase(repo).execute(
        company_id="c1", tier=PlanTier.PROFESSIONAL, billing_cycle=BillingCycle.YEARLY
    )
    assert sub.billing_cycle == BillingCycle.YEARLY


async def test_change_plan_is_idempotent_upsert() -> None:
    repo = FakeSubscriptionRepository()
    use_case = ChangePlanUseCase(repo)
    first = await use_case.execute(company_id="c1", tier=PlanTier.PROFESSIONAL)
    second = await use_case.execute(company_id="c1", tier=PlanTier.BUSINESS)
    assert first.id == second.id  # mesma linha, atualizada
    assert second.tier == PlanTier.BUSINESS
    assert len(await repo.list_all()) == 1


async def test_cancel_marks_canceled() -> None:
    repo = FakeSubscriptionRepository()
    await ChangePlanUseCase(repo).execute(company_id="c1", tier=PlanTier.BUSINESS)
    sub = await CancelSubscriptionUseCase(repo).execute(company_id="c1")
    assert sub.status == SubscriptionStatus.CANCELED
    assert sub.cancel_at_period_end is True
