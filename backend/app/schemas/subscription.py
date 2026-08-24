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
    # O teste já foi consumido: a tela precisa parar de oferecer "14 dias
    # grátis" para quem não pode mais aceitar.
    trial_used: bool = False
    # Há uma contratação aguardando pagamento. Sem isto, quem fechou a aba do
    # boleto voltaria para uma tela que não menciona a cobrança pendente.
    payment_pending: bool = False
    # Plano contratado mas ainda não pago. Diferente de `tier`, que é o plano
    # que a empresa realmente pode usar agora — quem deve não usa o que
    # contratou, mas precisa saber o que estava contratando para concluir.
    pending_tier: PlanTier | None = None


class ChangePlanRequest(BaseModel):
    tier: PlanTier
    billing_cycle: BillingCycle = BillingCycle.MONTHLY
    start_trial: bool = Field(
        default=False,
        description="Inicia um teste gratuito de 14 dias em vez de ativar imediatamente.",
    )
