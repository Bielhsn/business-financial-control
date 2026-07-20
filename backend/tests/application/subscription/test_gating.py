import pytest

from app.application.subscription.change_plan import ChangePlanUseCase
from app.application.subscription.gating import (
    ensure_can_add_integration,
    ensure_can_add_member,
    ensure_feature,
)
from app.core.exceptions import PlanLimitError
from app.domain.company.roles import CompanyRole
from app.domain.subscription.plans import Feature, PlanTier
from tests.fakes import (
    FakeCompanyMembershipRepository,
    FakeConnectionRepository,
    FakeSubscriptionRepository,
)

pytestmark = pytest.mark.anyio


async def test_ensure_feature_blocks_when_not_included() -> None:
    subs = FakeSubscriptionRepository()  # sem assinatura => Starter
    with pytest.raises(PlanLimitError) as exc:
        await ensure_feature(subs, company_id="c1", feature=Feature.ADVANCED_AI)
    assert exc.value.status_code == 402
    assert exc.value.details["upgrade_required"] is True


async def test_ensure_feature_allows_when_included() -> None:
    subs = FakeSubscriptionRepository()
    await ChangePlanUseCase(subs).execute(company_id="c1", tier=PlanTier.PROFESSIONAL)
    # Não deve levantar.
    await ensure_feature(subs, company_id="c1", feature=Feature.ADVANCED_AI)


async def test_ensure_can_add_member_respects_starter_limit() -> None:
    subs = FakeSubscriptionRepository()
    members = FakeCompanyMembershipRepository()
    await members.create(company_id="c1", user_id="u1", role=CompanyRole.OWNER)
    await members.create(company_id="c1", user_id="u2", role=CompanyRole.EMPLOYEE)
    # Starter permite 2 membros; já há 2 => bloqueia o terceiro.
    with pytest.raises(PlanLimitError):
        await ensure_can_add_member(subs, members, company_id="c1")


async def test_ensure_can_add_member_allows_upgraded_plan() -> None:
    subs = FakeSubscriptionRepository()
    await ChangePlanUseCase(subs).execute(company_id="c1", tier=PlanTier.PROFESSIONAL)
    members = FakeCompanyMembershipRepository()
    await members.create(company_id="c1", user_id="u1", role=CompanyRole.OWNER)
    await members.create(company_id="c1", user_id="u2", role=CompanyRole.EMPLOYEE)
    # Professional permite 5 => terceiro é liberado.
    await ensure_can_add_member(subs, members, company_id="c1")


async def test_ensure_can_add_integration_respects_starter_limit() -> None:
    subs = FakeSubscriptionRepository()
    connections = FakeConnectionRepository()
    await connections.upsert(provider="hotmart", encrypted_secrets="x", config={})
    # Starter permite 1 integração; já há 1 => bloqueia a segunda.
    with pytest.raises(PlanLimitError):
        await ensure_can_add_integration(subs, connections, company_id="c1")
