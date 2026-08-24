from datetime import datetime
from typing import Protocol

from app.domain.subscription.entities import BillingCycle, Subscription, SubscriptionStatus
from app.domain.subscription.plans import PlanTier


class SubscriptionRepository(Protocol):
    async def get_by_company(self, company_id: str) -> Subscription | None: ...

    async def upsert(
        self,
        *,
        company_id: str,
        tier: PlanTier,
        status: SubscriptionStatus,
        billing_cycle: BillingCycle,
        trial_ends_at: datetime | None,
        current_period_end: datetime | None,
        cancel_at_period_end: bool,
        external_id: str | None = None,
        trial_used: bool = False,
    ) -> Subscription: ...

    async def get_by_external_id(self, external_id: str) -> Subscription | None:
        """Localiza a assinatura pelo id no provedor de pagamento.

        É o caminho do webhook: o aviso chega identificando a assinatura no
        Asaas, não a empresa. Sem esta busca, o pagamento não tem como virar
        acesso liberado.
        """
        ...

    async def list_all(self) -> list[Subscription]:
        """Todas as assinaturas explícitas — usado pelo painel administrativo."""
        ...
