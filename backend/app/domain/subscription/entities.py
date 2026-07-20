from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from app.domain.subscription.plans import PlanTier


class SubscriptionStatus(StrEnum):
    TRIALING = "trialing"  # em período de teste de um plano pago
    ACTIVE = "active"  # assinatura ativa e paga
    PAST_DUE = "past_due"  # pagamento atrasado (inadimplente)
    CANCELED = "canceled"  # cancelada (cai para o plano padrão)


class BillingCycle(StrEnum):
    MONTHLY = "monthly"
    YEARLY = "yearly"


@dataclass
class Subscription:
    id: str
    company_id: str
    tier: PlanTier
    status: SubscriptionStatus
    billing_cycle: BillingCycle
    started_at: datetime
    updated_at: datetime
    trial_ends_at: datetime | None = None
    current_period_end: datetime | None = None
    cancel_at_period_end: bool = False
