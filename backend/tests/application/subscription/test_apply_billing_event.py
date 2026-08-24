"""Aviso de pagamento virando direito de acesso.

Este é o ponto onde dinheiro encontra permissão. Errar para um lado libera de
graça; errar para o outro bloqueia quem pagou. Os dois são caros, e o segundo
chega como reclamação.
"""

from datetime import UTC, datetime, timedelta

import pytest

from app.application.subscription.apply_billing_event import ApplyBillingEventUseCase
from app.domain.billing.ports import BillingEvent, BillingEventType
from app.domain.subscription.entities import BillingCycle, Subscription, SubscriptionStatus
from app.domain.subscription.plans import PlanTier

pytestmark = pytest.mark.anyio


class FakeSubscriptionRepository:
    def __init__(self, assinatura: Subscription | None) -> None:
        self._assinatura = assinatura
        self.upserts: list[dict[str, object]] = []

    async def get_by_external_id(self, external_id: str) -> Subscription | None:
        if self._assinatura and self._assinatura.external_id == external_id:
            return self._assinatura
        return None

    async def upsert(self, **campos: object) -> Subscription:
        self.upserts.append(campos)
        assert self._assinatura is not None
        return self._assinatura


def _assinatura(status: SubscriptionStatus, **extra: object) -> Subscription:
    agora = datetime.now(UTC)
    return Subscription(
        id="sub-1",
        company_id="empresa-1",
        tier=PlanTier.PROFESSIONAL,
        status=status,
        billing_cycle=BillingCycle.MONTHLY,
        started_at=agora,
        updated_at=agora,
        external_id="asaas_1",
        **extra,  # type: ignore[arg-type]
    )


async def test_payment_activates_and_sets_the_period() -> None:
    repo = FakeSubscriptionRepository(_assinatura(SubscriptionStatus.PAST_DUE))
    fim = datetime.now(UTC) + timedelta(days=30)

    await ApplyBillingEventUseCase(repo).execute(
        BillingEvent(type=BillingEventType.PAID, external_id="asaas_1", period_end=fim)
    )

    aplicado = repo.upserts[0]
    assert aplicado["status"] == SubscriptionStatus.ACTIVE
    assert aplicado["current_period_end"] == fim
    # Pagou: o teste acabou e o que vale agora é o período pago.
    assert aplicado["trial_ends_at"] is None


async def test_payment_without_a_date_projects_from_the_cycle() -> None:
    """Nem todo aviso traz o vencimento. Sem projeção, a assinatura ficaria
    ativa sem prazo — e a expiração nunca aconteceria."""
    repo = FakeSubscriptionRepository(_assinatura(SubscriptionStatus.PAST_DUE))

    await ApplyBillingEventUseCase(repo).execute(
        BillingEvent(type=BillingEventType.PAID, external_id="asaas_1", period_end=None)
    )

    fim = repo.upserts[0]["current_period_end"]
    assert isinstance(fim, datetime)
    assert fim > datetime.now(UTC) + timedelta(days=25)


async def test_overdue_marks_past_due_without_erasing_the_period() -> None:
    """`resolve_plan` já derruba PAST_DUE para o plano grátis; preservar a data
    ajuda o suporte a explicar desde quando."""
    ate = datetime.now(UTC) - timedelta(days=2)
    repo = FakeSubscriptionRepository(
        _assinatura(SubscriptionStatus.ACTIVE, current_period_end=ate)
    )

    await ApplyBillingEventUseCase(repo).execute(
        BillingEvent(type=BillingEventType.OVERDUE, external_id="asaas_1")
    )

    assert repo.upserts[0]["status"] == SubscriptionStatus.PAST_DUE
    assert repo.upserts[0]["current_period_end"] == ate


async def test_cancellation_marks_canceled() -> None:
    repo = FakeSubscriptionRepository(_assinatura(SubscriptionStatus.ACTIVE))

    await ApplyBillingEventUseCase(repo).execute(
        BillingEvent(type=BillingEventType.CANCELED, external_id="asaas_1")
    )

    assert repo.upserts[0]["status"] == SubscriptionStatus.CANCELED


async def test_repeated_event_produces_the_same_state() -> None:
    """Provedor reenvia webhook quando não recebe 200 a tempo. O mesmo
    pagamento chegando três vezes não pode render três períodos."""
    repo = FakeSubscriptionRepository(_assinatura(SubscriptionStatus.PAST_DUE))
    fim = datetime.now(UTC) + timedelta(days=30)
    evento = BillingEvent(type=BillingEventType.PAID, external_id="asaas_1", period_end=fim)

    caso = ApplyBillingEventUseCase(repo)
    await caso.execute(evento)
    await caso.execute(evento)
    await caso.execute(evento)

    # Estado calculado a partir do evento, nunca incrementado a partir do
    # anterior — três entregas, mesmo resultado.
    assert all(u["current_period_end"] == fim for u in repo.upserts)
    assert all(u["status"] == SubscriptionStatus.ACTIVE for u in repo.upserts)


async def test_unknown_subscription_is_ignored_without_crashing() -> None:
    """Cobrança criada fora do produto, ou webhook de outro ambiente apontando
    para cá. Estourar faria o provedor reenviar para sempre."""
    repo = FakeSubscriptionRepository(None)

    resultado = await ApplyBillingEventUseCase(repo).execute(
        BillingEvent(type=BillingEventType.PAID, external_id="desconhecida")
    )

    assert resultado is None
    assert repo.upserts == []
