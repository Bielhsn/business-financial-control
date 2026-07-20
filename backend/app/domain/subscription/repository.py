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
    ) -> Subscription: ...

    async def list_all(self) -> list[Subscription]:
        """Todas as assinaturas explícitas — usado pelo painel administrativo."""
        ...
