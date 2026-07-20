from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.subscription.entities import BillingCycle, SubscriptionStatus
from app.domain.subscription.plans import PlanTier


class PlanLimitsResponse(BaseModel):
    max_members: int
    max_integrations: int
    max_ai_insights_per_month: int
    max_catalog_items: int


class PlanResponse(BaseModel):
    tier: PlanTier
    name: str
    tagline: str
    target_audience: str
    price_cents_monthly: int
    price_cents_yearly: int
    limits: PlanLimitsResponse
    features: list[str]
    highlights: list[str]
    is_contact_sales: bool
    badge: str | None = None


class PlanCatalogResponse(BaseModel):
    plans: list[PlanResponse]


class UsageResponse(BaseModel):
    """Uso atual x limite, para o frontend desenhar barras de consumo."""

    members: int
    integrations: int


class SubscriptionResponse(BaseModel):
    tier: PlanTier
    status: SubscriptionStatus
    billing_cycle: BillingCycle
    trial_ends_at: datetime | None
    current_period_end: datetime | None
    cancel_at_period_end: bool
    features: list[str]
    limits: PlanLimitsResponse
    usage: UsageResponse


class ChangePlanRequest(BaseModel):
    tier: PlanTier
    billing_cycle: BillingCycle = BillingCycle.MONTHLY
    start_trial: bool = Field(
        default=False,
        description="Inicia um teste gratuito de 14 dias em vez de ativar imediatamente.",
    )
