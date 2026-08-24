from pydantic import BaseModel

from app.domain.subscription.entities import BillingCycle
from app.domain.subscription.plans import PlanTier


class CheckoutRequest(BaseModel):
    tier: PlanTier
    billing_cycle: BillingCycle = BillingCycle.MONTHLY


class CheckoutResponse(BaseModel):
    """Para onde mandar o lojista pagar. O status da assinatura só muda quando
    o dinheiro entra — quem decide é o webhook, não esta resposta."""

    payment_url: str
