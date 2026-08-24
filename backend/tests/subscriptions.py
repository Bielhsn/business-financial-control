"""Ajudantes para colocar uma empresa num plano pago dentro dos testes.

Antes isto era feito chamando `ChangePlanUseCase` com um plano pago — o mesmo
atalho que existia no produto e que dava plano Business de graça a quem
clicasse. Fechado o buraco, os testes que só precisavam de uma empresa "no
Profissional" escrevem o estado direto, como o webhook de pagamento faria.
"""

import asyncio
from datetime import UTC, datetime, timedelta

from app.domain.subscription.entities import BillingCycle, Subscription, SubscriptionStatus
from app.domain.subscription.plans import PlanTier
from app.domain.subscription.repository import SubscriptionRepository

_CICLO = {BillingCycle.MONTHLY: timedelta(days=30), BillingCycle.YEARLY: timedelta(days=365)}


async def activate_paid_plan(
    repository: SubscriptionRepository,
    *,
    company_id: str,
    tier: PlanTier,
    billing_cycle: BillingCycle = BillingCycle.MONTHLY,
    external_id: str | None = None,
) -> Subscription:
    """Assinatura paga e em dia, como fica depois de o pagamento ser confirmado."""
    return await repository.upsert(
        company_id=company_id,
        tier=tier,
        status=SubscriptionStatus.ACTIVE,
        billing_cycle=billing_cycle,
        trial_ends_at=None,
        current_period_end=datetime.now(UTC) + _CICLO[billing_cycle],
        cancel_at_period_end=False,
        external_id=external_id,
    )


def activate_paid_plan_sync(
    repository: SubscriptionRepository,
    *,
    company_id: str,
    tier: PlanTier,
    billing_cycle: BillingCycle = BillingCycle.MONTHLY,
    external_id: str | None = None,
) -> Subscription:
    """Versão para os testes de API, que rodam síncronos com o `TestClient`.

    Escreve direto no repositório em vez de chamar o endpoint: contratar plano
    pago por HTTP exige pagamento, e o que estes testes precisam é do *estado*
    de quem já pagou, não do caminho até lá.
    """
    return asyncio.run(
        activate_paid_plan(
            repository,
            company_id=company_id,
            tier=tier,
            billing_cycle=billing_cycle,
            external_id=external_id,
        )
    )
