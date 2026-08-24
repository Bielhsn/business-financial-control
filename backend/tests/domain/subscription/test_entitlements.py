from datetime import UTC, datetime, timedelta

from app.domain.subscription.entities import BillingCycle, Subscription, SubscriptionStatus
from app.domain.subscription.entitlements import (
    build_entitlements,
    check_integrations,
    check_members,
    has_feature,
    resolve_plan,
)
from app.domain.subscription.plans import UNLIMITED, Feature, PlanTier, get_plan


def _sub(tier: PlanTier, status: SubscriptionStatus) -> Subscription:
    now = datetime.now(UTC)
    return Subscription(
        id="1",
        company_id="c1",
        tier=tier,
        status=status,
        billing_cycle=BillingCycle.MONTHLY,
        started_at=now,
        updated_at=now,
    )


def test_no_subscription_resolves_to_starter() -> None:
    plan = resolve_plan(None)
    assert plan.tier == PlanTier.STARTER


def test_canceled_subscription_falls_back_to_starter() -> None:
    sub = _sub(PlanTier.BUSINESS, SubscriptionStatus.CANCELED)
    assert resolve_plan(sub).tier == PlanTier.STARTER


def test_past_due_subscription_falls_back_to_starter() -> None:
    sub = _sub(PlanTier.PROFESSIONAL, SubscriptionStatus.PAST_DUE)
    assert resolve_plan(sub).tier == PlanTier.STARTER


def test_active_and_trialing_keep_contracted_plan() -> None:
    active = _sub(PlanTier.BUSINESS, SubscriptionStatus.ACTIVE)
    trialing = _sub(PlanTier.PROFESSIONAL, SubscriptionStatus.TRIALING)
    assert resolve_plan(active).tier == PlanTier.BUSINESS
    assert resolve_plan(trialing).tier == PlanTier.PROFESSIONAL


def test_feature_gating_by_plan() -> None:
    assert has_feature(None, Feature.ADVANCED_AI) is False  # Starter
    pro = _sub(PlanTier.PROFESSIONAL, SubscriptionStatus.ACTIVE)
    assert has_feature(pro, Feature.ADVANCED_AI) is True
    assert has_feature(pro, Feature.WHITE_LABEL) is False  # só Business+


def test_enterprise_has_every_feature() -> None:
    ent = _sub(PlanTier.ENTERPRISE, SubscriptionStatus.ACTIVE)
    for feature in Feature:
        assert has_feature(ent, feature) is True


def test_member_limit_check() -> None:
    # Starter: max_members=2
    assert check_members(None, current_count=1).allowed is True
    assert check_members(None, current_count=2).allowed is False


def test_integration_limit_check() -> None:
    # Starter: max_integrations=1
    assert check_integrations(None, current_count=0).allowed is True
    assert check_integrations(None, current_count=1).allowed is False


def test_unlimited_is_never_blocked() -> None:
    ent = _sub(PlanTier.ENTERPRISE, SubscriptionStatus.ACTIVE)
    assert get_plan(PlanTier.ENTERPRISE).limits.max_members == UNLIMITED
    assert check_members(ent, current_count=9999).allowed is True
    assert check_integrations(ent, current_count=9999).allowed is True


def test_build_entitlements_mirrors_plan() -> None:
    pro = _sub(PlanTier.PROFESSIONAL, SubscriptionStatus.ACTIVE)
    ent = build_entitlements(pro)
    plan = get_plan(PlanTier.PROFESSIONAL)
    assert ent.tier == PlanTier.PROFESSIONAL
    assert ent.max_members == plan.limits.max_members
    assert ent.features == plan.features


# --- O prazo precisa valer ------------------------------------------------
#
# `trial_ends_at` e `current_period_end` eram gravados e nunca lidos: um teste
# iniciado ficava TRIALING para sempre, e todo "teste de 14 dias" virava plano
# pago vitalício de graça. Mesmo padrão do refresh de OAuth — campo persistido
# sem ninguém consultar.


def _assinatura(
    status: SubscriptionStatus,
    *,
    trial_ends_at: datetime | None = None,
    current_period_end: datetime | None = None,
) -> Subscription:
    agora = datetime.now(UTC)
    return Subscription(
        id="sub-1",
        company_id="empresa-1",
        tier=PlanTier.PROFESSIONAL,
        status=status,
        billing_cycle=BillingCycle.MONTHLY,
        started_at=agora,
        updated_at=agora,
        trial_ends_at=trial_ends_at,
        current_period_end=current_period_end,
    )


def test_expired_trial_falls_back_to_the_free_plan() -> None:
    vencido = _assinatura(
        SubscriptionStatus.TRIALING, trial_ends_at=datetime.now(UTC) - timedelta(days=1)
    )

    assert resolve_plan(vencido).tier == PlanTier.STARTER


def test_trial_still_running_keeps_the_paid_plan() -> None:
    vigente = _assinatura(
        SubscriptionStatus.TRIALING, trial_ends_at=datetime.now(UTC) + timedelta(days=5)
    )

    assert resolve_plan(vigente).tier == PlanTier.PROFESSIONAL


def test_paid_subscription_keeps_a_short_grace_after_the_period() -> None:
    """Processador repete cobrança e webhook atrasa. Cortar no segundo exato
    puniria quem está em dia por causa de latência de terceiro."""
    recem_vencida = _assinatura(
        SubscriptionStatus.ACTIVE, current_period_end=datetime.now(UTC) - timedelta(days=1)
    )

    assert resolve_plan(recem_vencida).tier == PlanTier.PROFESSIONAL


def test_paid_subscription_expires_after_the_grace() -> None:
    abandonada = _assinatura(
        SubscriptionStatus.ACTIVE, current_period_end=datetime.now(UTC) - timedelta(days=30)
    )

    assert resolve_plan(abandonada).tier == PlanTier.STARTER


def test_subscription_without_deadline_is_not_treated_as_expired() -> None:
    """Assinatura sem data (ex.: cortesia) não pode ser derrubada por engano."""
    sem_prazo = _assinatura(SubscriptionStatus.ACTIVE)

    assert resolve_plan(sem_prazo).tier == PlanTier.PROFESSIONAL


def test_features_follow_the_expired_plan() -> None:
    """Não basta o plano cair: o recurso pago precisa fechar junto, senão a
    expiração seria cosmética."""
    vencido = _assinatura(
        SubscriptionStatus.TRIALING, trial_ends_at=datetime.now(UTC) - timedelta(days=1)
    )

    assert has_feature(vencido, Feature.WHITE_LABEL) is False
