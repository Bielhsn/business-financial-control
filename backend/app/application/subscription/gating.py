"""Verificações de gating reutilizáveis pela API.

Cada função carrega a assinatura efetiva da empresa e aplica um limite/feature,
levantando PlanLimitError (402) com detalhes para o frontend oferecer upgrade.
"""

from app.core.exceptions import PlanLimitError
from app.domain.company.repository import CompanyMembershipRepository
from app.domain.connector.repository import ConnectionRepository
from app.domain.subscription.entitlements import (
    check_integrations,
    check_members,
    has_feature,
    resolve_plan,
)
from app.domain.subscription.plans import Feature
from app.domain.subscription.repository import SubscriptionRepository


def _upgrade_details(company_id: str, **extra: object) -> dict[str, object]:
    return {"company_id": company_id, "upgrade_required": True, **extra}


async def ensure_feature(
    subscription_repository: SubscriptionRepository,
    *,
    company_id: str,
    feature: Feature,
) -> None:
    subscription = await subscription_repository.get_by_company(company_id)
    if not has_feature(subscription, feature):
        plan = resolve_plan(subscription)
        raise PlanLimitError(
            f"Este recurso não está incluído no plano {plan.name}. "
            "Faça upgrade para desbloquear.",
            details=_upgrade_details(company_id, feature=feature.value, current_tier=plan.tier),
        )


async def ensure_can_add_integration(
    subscription_repository: SubscriptionRepository,
    connection_repository: ConnectionRepository,
    *,
    company_id: str,
) -> None:
    subscription = await subscription_repository.get_by_company(company_id)
    await ensure_feature(
        subscription_repository, company_id=company_id, feature=Feature.INTEGRATIONS
    )
    connections = await connection_repository.list_all()
    result = check_integrations(subscription, len(connections))
    if not result.allowed:
        plan = resolve_plan(subscription)
        raise PlanLimitError(
            f"Você atingiu o limite de {result.limit} integração(ões) do plano {plan.name}. "
            "Faça upgrade para conectar mais plataformas.",
            details=_upgrade_details(
                company_id, limit=result.limit, current=result.current, current_tier=plan.tier
            ),
        )


async def ensure_can_add_member(
    subscription_repository: SubscriptionRepository,
    membership_repository: CompanyMembershipRepository,
    *,
    company_id: str,
) -> None:
    subscription = await subscription_repository.get_by_company(company_id)
    members = await membership_repository.list_for_company(company_id)
    result = check_members(subscription, len(members))
    if not result.allowed:
        plan = resolve_plan(subscription)
        raise PlanLimitError(
            f"Você atingiu o limite de {result.limit} usuário(s) do plano {plan.name}. "
            "Faça upgrade para adicionar mais membros à equipe.",
            details=_upgrade_details(
                company_id, limit=result.limit, current=result.current, current_tier=plan.tier
            ),
        )
