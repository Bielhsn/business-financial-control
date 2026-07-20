from datetime import UTC, datetime, timedelta

from app.domain.subscription.entities import BillingCycle, Subscription, SubscriptionStatus
from app.domain.subscription.plans import PlanTier
from app.domain.subscription.repository import SubscriptionRepository

_TRIAL_DAYS = 14


class ChangePlanUseCase:
    """Troca o plano de uma empresa (upgrade/downgrade) ou inicia um teste.

    A cobrança real (Stripe) entra numa etapa futura; por ora a assinatura é
    marcada como ativa (ou em teste) imediatamente, registrando o período para o
    painel administrativo calcular MRR/renovações.
    """

    def __init__(self, subscription_repository: SubscriptionRepository) -> None:
        self._subscription_repository = subscription_repository

    async def execute(
        self,
        *,
        company_id: str,
        tier: PlanTier,
        billing_cycle: BillingCycle = BillingCycle.MONTHLY,
        start_trial: bool = False,
    ) -> Subscription:
        now = datetime.now(UTC)

        if tier == PlanTier.STARTER:
            # Plano grátis: sempre ativo, sem período nem teste.
            return await self._subscription_repository.upsert(
                company_id=company_id,
                tier=tier,
                status=SubscriptionStatus.ACTIVE,
                billing_cycle=billing_cycle,
                trial_ends_at=None,
                current_period_end=None,
                cancel_at_period_end=False,
            )

        if start_trial:
            trial_ends_at = now + timedelta(days=_TRIAL_DAYS)
            return await self._subscription_repository.upsert(
                company_id=company_id,
                tier=tier,
                status=SubscriptionStatus.TRIALING,
                billing_cycle=billing_cycle,
                trial_ends_at=trial_ends_at,
                current_period_end=trial_ends_at,
                cancel_at_period_end=False,
            )

        period = timedelta(days=365 if billing_cycle == BillingCycle.YEARLY else 30)
        return await self._subscription_repository.upsert(
            company_id=company_id,
            tier=tier,
            status=SubscriptionStatus.ACTIVE,
            billing_cycle=billing_cycle,
            trial_ends_at=None,
            current_period_end=now + period,
            cancel_at_period_end=False,
        )


class CancelSubscriptionUseCase:
    """Cancela a assinatura ao fim do período — a empresa cai para o Starter
    quando o período corrente expira. Cancelamento imediato marca CANCELED."""

    def __init__(self, subscription_repository: SubscriptionRepository) -> None:
        self._subscription_repository = subscription_repository

    async def execute(self, *, company_id: str) -> Subscription:
        current = await self._subscription_repository.get_by_company(company_id)
        tier = current.tier if current else PlanTier.STARTER
        billing_cycle = current.billing_cycle if current else BillingCycle.MONTHLY
        return await self._subscription_repository.upsert(
            company_id=company_id,
            tier=tier,
            status=SubscriptionStatus.CANCELED,
            billing_cycle=billing_cycle,
            trial_ends_at=None,
            current_period_end=current.current_period_end if current else None,
            cancel_at_period_end=True,
        )
