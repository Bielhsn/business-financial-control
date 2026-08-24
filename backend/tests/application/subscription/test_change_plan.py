"""Mudança de plano fora do pagamento.

O teste central aqui é o que **recusa**: enquanto ativar um plano pago era só
uma chamada, o produto inteiro saía de graça para quem clicasse em "Assinar".
"""

import pytest

from app.application.subscription.change_plan import (
    CancelSubscriptionUseCase,
    ChangePlanUseCase,
)
from app.core.exceptions import ValidationError
from app.domain.subscription.entities import BillingCycle, SubscriptionStatus
from app.domain.subscription.plans import PlanTier
from tests.fakes import FakeSubscriptionRepository
from tests.subscriptions import activate_paid_plan

pytestmark = pytest.mark.anyio


async def test_paid_plan_cannot_be_activated_without_payment() -> None:
    repo = FakeSubscriptionRepository()

    with pytest.raises(ValidationError, match="checkout"):
        await ChangePlanUseCase(repo).execute(company_id="c1", tier=PlanTier.PROFESSIONAL)

    # E não deixa rastro: nada de assinatura meio criada.
    assert await repo.list_all() == []


async def test_start_trial_sets_trialing_status() -> None:
    repo = FakeSubscriptionRepository()
    sub = await ChangePlanUseCase(repo).execute(
        company_id="c1", tier=PlanTier.BUSINESS, start_trial=True
    )
    assert sub.status == SubscriptionStatus.TRIALING
    assert sub.trial_ends_at is not None
    assert sub.trial_used is True


async def test_trial_cannot_be_started_twice() -> None:
    repo = FakeSubscriptionRepository()
    use_case = ChangePlanUseCase(repo)
    await use_case.execute(company_id="c1", tier=PlanTier.BUSINESS, start_trial=True)

    with pytest.raises(ValidationError, match="já foi utilizado"):
        await use_case.execute(company_id="c1", tier=PlanTier.PROFESSIONAL, start_trial=True)


async def test_going_back_to_starter_does_not_restore_the_trial() -> None:
    """O caminho óbvio para 14 dias infinitos: testar, descer para o grátis e
    testar de novo. O histórico do teste precisa sobreviver ao downgrade."""
    repo = FakeSubscriptionRepository()
    use_case = ChangePlanUseCase(repo)
    await use_case.execute(company_id="c1", tier=PlanTier.BUSINESS, start_trial=True)
    await use_case.execute(company_id="c1", tier=PlanTier.STARTER)

    with pytest.raises(ValidationError, match="já foi utilizado"):
        await use_case.execute(company_id="c1", tier=PlanTier.BUSINESS, start_trial=True)


async def test_cancelling_does_not_restore_the_trial() -> None:
    repo = FakeSubscriptionRepository()
    await ChangePlanUseCase(repo).execute(company_id="c1", tier=PlanTier.BUSINESS, start_trial=True)
    await CancelSubscriptionUseCase(repo).execute(company_id="c1")

    with pytest.raises(ValidationError, match="já foi utilizado"):
        await ChangePlanUseCase(repo).execute(
            company_id="c1", tier=PlanTier.BUSINESS, start_trial=True
        )


async def test_starter_never_has_trial_or_period() -> None:
    repo = FakeSubscriptionRepository()
    sub = await ChangePlanUseCase(repo).execute(
        company_id="c1", tier=PlanTier.STARTER, start_trial=True
    )
    assert sub.status == SubscriptionStatus.ACTIVE
    assert sub.trial_ends_at is None
    assert sub.current_period_end is None
    # Pedir teste do plano grátis não consome o teste — não há o que testar.
    assert sub.trial_used is False


async def test_trial_keeps_the_chosen_cycle() -> None:
    repo = FakeSubscriptionRepository()
    sub = await ChangePlanUseCase(repo).execute(
        company_id="c1",
        tier=PlanTier.PROFESSIONAL,
        billing_cycle=BillingCycle.YEARLY,
        start_trial=True,
    )
    assert sub.billing_cycle == BillingCycle.YEARLY


async def test_change_plan_is_idempotent_upsert() -> None:
    repo = FakeSubscriptionRepository()
    first = await activate_paid_plan(repo, company_id="c1", tier=PlanTier.PROFESSIONAL)
    second = await ChangePlanUseCase(repo).execute(company_id="c1", tier=PlanTier.STARTER)
    assert first.id == second.id  # mesma linha, atualizada
    assert second.tier == PlanTier.STARTER
    assert len(await repo.list_all()) == 1


async def test_cancel_marks_canceled() -> None:
    repo = FakeSubscriptionRepository()
    await activate_paid_plan(repo, company_id="c1", tier=PlanTier.BUSINESS)
    sub = await CancelSubscriptionUseCase(repo).execute(company_id="c1")
    assert sub.status == SubscriptionStatus.CANCELED
    assert sub.cancel_at_period_end is True


async def test_cancel_keeps_the_billing_link() -> None:
    """O vínculo com o provedor é o que permite o webhook de cancelamento
    encontrar a assinatura depois."""
    repo = FakeSubscriptionRepository()
    await activate_paid_plan(repo, company_id="c1", tier=PlanTier.BUSINESS, external_id="asaas_1")
    sub = await CancelSubscriptionUseCase(repo).execute(company_id="c1")
    assert sub.external_id == "asaas_1"
