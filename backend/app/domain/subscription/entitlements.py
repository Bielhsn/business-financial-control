"""Resolução de direitos (entitlements) de uma empresa a partir da assinatura.

Lógica pura e sem I/O: recebe a assinatura (ou None) e devolve o plano efetivo,
além de checagens de funcionalidade e limite. É o coração do gating — a API e o
frontend consultam isto para liberar/bloquear recursos.
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.domain.subscription.entities import Subscription, SubscriptionStatus
from app.domain.subscription.plans import (
    UNLIMITED,
    Feature,
    PlanDefinition,
    PlanTier,
    default_plan,
    get_plan,
)

# Status que mantêm o plano contratado ativo. CANCELED/PAST_DUE derrubam para o
# plano padrão (Starter), bloqueando os recursos pagos até regularizar.
_ENTITLED_STATUSES = frozenset({SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING})


# Tolerância para assinatura paga cujo período venceu. Processador de pagamento
# repete cobrança e webhook chega atrasado; cortar o acesso no segundo exato
# puniria quem está em dia por causa de latência de terceiro. Para o teste
# gratuito não há tolerância — a data de fim é o combinado.
_PAYMENT_GRACE = timedelta(days=3)


def _is_within_term(subscription: Subscription, now: datetime) -> bool:
    """O prazo da assinatura ainda vale?

    Havia um buraco silencioso aqui: `trial_ends_at` e `current_period_end`
    eram gravados e nunca lidos. Um teste iniciado ficava TRIALING para sempre,
    então todo "teste de 14 dias" era, na prática, plano pago vitalício de
    graça.
    """
    if subscription.status == SubscriptionStatus.TRIALING:
        return subscription.trial_ends_at is None or now <= subscription.trial_ends_at
    if subscription.status == SubscriptionStatus.ACTIVE:
        return (
            subscription.current_period_end is None
            or now <= subscription.current_period_end + _PAYMENT_GRACE
        )
    return False


def resolve_plan(
    subscription: Subscription | None, *, now: datetime | None = None
) -> PlanDefinition:
    """Plano efetivo de uma empresa. Sem assinatura, inadimplente, cancelada ou
    com o prazo vencido, a empresa fica no plano padrão (Starter)."""
    if subscription is None:
        return default_plan()
    if subscription.status not in _ENTITLED_STATUSES:
        return default_plan()
    if not _is_within_term(subscription, now or datetime.now(UTC)):
        return default_plan()
    return get_plan(subscription.tier)


@dataclass(frozen=True)
class LimitCheck:
    allowed: bool
    limit: int  # UNLIMITED (-1) quando não há teto
    current: int


def has_feature(subscription: Subscription | None, feature: Feature) -> bool:
    return resolve_plan(subscription).has_feature(feature)


def _within(limit: int, current: int) -> bool:
    if limit == UNLIMITED:
        return True
    return current < limit


def check_members(subscription: Subscription | None, current_count: int) -> LimitCheck:
    limit = resolve_plan(subscription).limits.max_members
    return LimitCheck(allowed=_within(limit, current_count), limit=limit, current=current_count)


def check_integrations(subscription: Subscription | None, current_count: int) -> LimitCheck:
    limit = resolve_plan(subscription).limits.max_integrations
    return LimitCheck(allowed=_within(limit, current_count), limit=limit, current=current_count)


def check_catalog_items(subscription: Subscription | None, current_count: int) -> LimitCheck:
    limit = resolve_plan(subscription).limits.max_catalog_items
    return LimitCheck(allowed=_within(limit, current_count), limit=limit, current=current_count)


@dataclass(frozen=True)
class Entitlements:
    """Visão consolidada dos direitos de uma empresa — serializada para o
    frontend renderizar cadeados e a barra de uso."""

    tier: PlanTier
    features: frozenset[Feature]
    max_members: int
    max_integrations: int
    max_ai_insights_per_month: int
    max_catalog_items: int


def build_entitlements(subscription: Subscription | None) -> Entitlements:
    plan = resolve_plan(subscription)
    return Entitlements(
        tier=plan.tier,
        features=plan.features,
        max_members=plan.limits.max_members,
        max_integrations=plan.limits.max_integrations,
        max_ai_insights_per_month=plan.limits.max_ai_insights_per_month,
        max_catalog_items=plan.limits.max_catalog_items,
    )
