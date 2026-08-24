"""Mudança de plano fora do fluxo de pagamento.

Este caso de uso cobre exatamente três movimentos: voltar para o Starter,
iniciar o teste gratuito e cancelar. **Ativar um plano pago não está aqui** —
isso passa pelo checkout, e quem muda o status é o webhook do provedor.

A separação não é estética. Até aqui, `PUT /subscription` com
`tier=business` devolvia 30 dias de plano Business ativo sem ninguém pagar
nada, e o botão "Assinar" da tela de planos chamava exatamente isso. O produto
inteiro era gratuito para quem clicasse.
"""

from datetime import UTC, datetime, timedelta

from app.core.exceptions import ValidationError
from app.domain.subscription.entities import BillingCycle, Subscription, SubscriptionStatus
from app.domain.subscription.plans import PlanTier
from app.domain.subscription.repository import SubscriptionRepository

_TRIAL_DAYS = 14


class ChangePlanUseCase:
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
        atual = await self._subscription_repository.get_by_company(company_id)
        trial_used = atual.trial_used if atual else False

        if tier == PlanTier.STARTER:
            # Plano grátis: sempre ativo, sem período nem teste. O histórico do
            # teste sobrevive à volta para o Starter — senão bastaria descer e
            # subir para ganhar mais 14 dias.
            return await self._subscription_repository.upsert(
                company_id=company_id,
                tier=tier,
                status=SubscriptionStatus.ACTIVE,
                billing_cycle=billing_cycle,
                trial_ends_at=None,
                current_period_end=None,
                cancel_at_period_end=False,
                trial_used=trial_used,
            )

        if not start_trial:
            raise ValidationError(
                "Planos pagos são contratados pelo checkout, não por troca direta de plano."
            )

        if trial_used:
            raise ValidationError("O teste gratuito desta empresa já foi utilizado.")

        trial_ends_at = datetime.now(UTC) + timedelta(days=_TRIAL_DAYS)
        return await self._subscription_repository.upsert(
            company_id=company_id,
            tier=tier,
            status=SubscriptionStatus.TRIALING,
            billing_cycle=billing_cycle,
            trial_ends_at=trial_ends_at,
            current_period_end=trial_ends_at,
            cancel_at_period_end=False,
            trial_used=True,
        )


class CancelSubscriptionUseCase:
    """Cancela a assinatura localmente.

    Quem cancela a cobrança no provedor é o router, **antes** de chamar isto:
    marcar como cancelado aqui e continuar sendo cobrado lá seria o pior
    resultado possível para o cliente.
    """

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
            trial_used=current.trial_used if current else False,
        )
