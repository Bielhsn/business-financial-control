"""Traduz aviso do provedor de pagamento em direito de acesso.

É o elo que faltava: até aqui a assinatura era marcada como ativa sem ninguém
pagar nada. Agora quem decide o status é o dinheiro — pagou, renova; venceu sem
pagar, cai para inadimplente; cancelou, encerra.

**Idempotência importa aqui.** Provedor reenvia webhook quando não recebe 200 a
tempo, e o mesmo pagamento pode chegar duas ou três vezes. Aplicar o mesmo
efeito de novo tem que ser inofensivo — por isso o estado é calculado a partir
do evento, nunca incrementado a partir do estado anterior.
"""

from datetime import UTC, datetime, timedelta

from app.core.logging import get_logger
from app.domain.billing.ports import BillingEvent, BillingEventType
from app.domain.subscription.entities import BillingCycle, Subscription, SubscriptionStatus
from app.domain.subscription.repository import SubscriptionRepository

logger = get_logger(__name__)

_PERIODO = {BillingCycle.MONTHLY: timedelta(days=30), BillingCycle.YEARLY: timedelta(days=365)}


class ApplyBillingEventUseCase:
    def __init__(self, subscription_repository: SubscriptionRepository) -> None:
        self._subscriptions = subscription_repository

    async def execute(self, event: BillingEvent) -> Subscription | None:
        assinatura = await self._subscriptions.get_by_external_id(event.external_id)
        if assinatura is None:
            # Aviso de uma assinatura que não conhecemos. Pode ser cobrança
            # criada fora do produto ou webhook de outro ambiente apontando para
            # cá — registrar e ignorar é melhor que estourar e fazer o provedor
            # reenviar para sempre.
            logger.warning("billing_event_unknown_subscription", external_id=event.external_id)
            return None

        status, period_end = _resolve(event, assinatura)
        logger.info(
            "billing_event_applied",
            company_id=assinatura.company_id,
            # `event` é reservado pelo structlog (é o nome da mensagem).
            billing_event=event.type.value,
            status=status.value,
        )
        return await self._subscriptions.upsert(
            company_id=assinatura.company_id,
            tier=assinatura.tier,
            status=status,
            billing_cycle=assinatura.billing_cycle,
            # Pagou: o teste acabou, o que vale agora é o período pago.
            trial_ends_at=None if status == SubscriptionStatus.ACTIVE else assinatura.trial_ends_at,
            current_period_end=period_end,
            cancel_at_period_end=assinatura.cancel_at_period_end,
            external_id=assinatura.external_id,
        )


def _resolve(
    event: BillingEvent, atual: Subscription
) -> tuple[SubscriptionStatus, datetime | None]:
    if event.type == BillingEventType.PAID:
        # O fim do período vem do provedor quando ele informa; senão, projeta
        # pelo ciclo contratado. Confiar só no cálculo local desalinharia do
        # que o cliente realmente pagou.
        fim = event.period_end or datetime.now(UTC) + _PERIODO[atual.billing_cycle]
        return SubscriptionStatus.ACTIVE, fim
    if event.type == BillingEventType.OVERDUE:
        # Não zera o período: `resolve_plan` já derruba PAST_DUE para o plano
        # grátis, e preservar a data ajuda o suporte a explicar desde quando.
        return SubscriptionStatus.PAST_DUE, atual.current_period_end
    return SubscriptionStatus.CANCELED, atual.current_period_end
