from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.v1.deps import (
    get_audit_log_repository,
    get_company_context,
    get_company_membership_repository,
    get_connection_repository,
    get_current_user,
    get_subscription_repository,
    require_role,
)
from app.api.v1.routers.plans import to_plan_response
from app.application.subscription.change_plan import (
    CancelSubscriptionUseCase,
    ChangePlanUseCase,
)
from app.core.audit import record_audit
from app.core.tenant import CompanyContext
from app.domain.audit.repository import AuditLogRepository
from app.domain.company.repository import CompanyMembershipRepository
from app.domain.company.roles import CompanyRole
from app.domain.connector.repository import ConnectionRepository
from app.domain.subscription.entities import BillingCycle, Subscription, SubscriptionStatus
from app.domain.subscription.entitlements import resolve_plan
from app.domain.subscription.plans import get_plan
from app.domain.subscription.repository import SubscriptionRepository
from app.domain.user.entities import User
from app.schemas.subscription import (
    ChangePlanRequest,
    PlanLimitsResponse,
    PlanResponse,
    SubscriptionResponse,
    UsageResponse,
)

router = APIRouter(prefix="/companies/{company_id}/subscription", tags=["subscription"])

_OWNER = (CompanyRole.OWNER,)


async def _build_response(
    subscription: Subscription | None,
    *,
    membership_repository: CompanyMembershipRepository,
    connection_repository: ConnectionRepository,
    company_id: str,
) -> SubscriptionResponse:
    plan = resolve_plan(subscription)
    members = await membership_repository.list_for_company(company_id)
    connections = await connection_repository.list_all()
    return SubscriptionResponse(
        tier=plan.tier,
        status=subscription.status if subscription else SubscriptionStatus.ACTIVE,
        billing_cycle=subscription.billing_cycle if subscription else BillingCycle.MONTHLY,
        trial_ends_at=subscription.trial_ends_at if subscription else None,
        current_period_end=subscription.current_period_end if subscription else None,
        cancel_at_period_end=subscription.cancel_at_period_end if subscription else False,
        features=[feature.value for feature in plan.features],
        limits=PlanLimitsResponse(
            max_members=plan.limits.max_members,
            max_integrations=plan.limits.max_integrations,
            max_ai_insights_per_month=plan.limits.max_ai_insights_per_month,
            max_catalog_items=plan.limits.max_catalog_items,
        ),
        usage=UsageResponse(members=len(members), integrations=len(connections)),
    )


@router.get("", response_model=SubscriptionResponse)
async def get_subscription(
    company_context: Annotated[CompanyContext, Depends(get_company_context)],
    subscription_repository: Annotated[
        SubscriptionRepository, Depends(get_subscription_repository)
    ],
    membership_repository: Annotated[
        CompanyMembershipRepository, Depends(get_company_membership_repository)
    ],
    connection_repository: Annotated[ConnectionRepository, Depends(get_connection_repository)],
) -> SubscriptionResponse:
    subscription = await subscription_repository.get_by_company(company_context.company_id)
    return await _build_response(
        subscription,
        membership_repository=membership_repository,
        connection_repository=connection_repository,
        company_id=company_context.company_id,
    )


@router.get("/current-plan", response_model=PlanResponse)
async def get_current_plan(
    company_context: Annotated[CompanyContext, Depends(get_company_context)],
    subscription_repository: Annotated[
        SubscriptionRepository, Depends(get_subscription_repository)
    ],
) -> PlanResponse:
    subscription = await subscription_repository.get_by_company(company_context.company_id)
    return to_plan_response(resolve_plan(subscription))


@router.put("", response_model=SubscriptionResponse)
async def change_plan(
    payload: ChangePlanRequest,
    company_context: Annotated[CompanyContext, Depends(require_role(*_OWNER))],
    current_user: Annotated[User, Depends(get_current_user)],
    subscription_repository: Annotated[
        SubscriptionRepository, Depends(get_subscription_repository)
    ],
    membership_repository: Annotated[
        CompanyMembershipRepository, Depends(get_company_membership_repository)
    ],
    connection_repository: Annotated[ConnectionRepository, Depends(get_connection_repository)],
    audit_repository: Annotated[AuditLogRepository, Depends(get_audit_log_repository)],
) -> SubscriptionResponse:
    use_case = ChangePlanUseCase(subscription_repository)
    subscription = await use_case.execute(
        company_id=company_context.company_id,
        tier=payload.tier,
        billing_cycle=payload.billing_cycle,
        start_trial=payload.start_trial,
    )
    await record_audit(
        audit_repository,
        "subscription_changed",
        user_id=current_user.id,
        company_id=company_context.company_id,
        tier=payload.tier.value,
        plan_name=get_plan(payload.tier).name,
    )
    return await _build_response(
        subscription,
        membership_repository=membership_repository,
        connection_repository=connection_repository,
        company_id=company_context.company_id,
    )


@router.delete("", response_model=SubscriptionResponse)
async def cancel_subscription(
    company_context: Annotated[CompanyContext, Depends(require_role(*_OWNER))],
    current_user: Annotated[User, Depends(get_current_user)],
    subscription_repository: Annotated[
        SubscriptionRepository, Depends(get_subscription_repository)
    ],
    membership_repository: Annotated[
        CompanyMembershipRepository, Depends(get_company_membership_repository)
    ],
    connection_repository: Annotated[ConnectionRepository, Depends(get_connection_repository)],
    audit_repository: Annotated[AuditLogRepository, Depends(get_audit_log_repository)],
) -> SubscriptionResponse:
    use_case = CancelSubscriptionUseCase(subscription_repository)
    subscription = await use_case.execute(company_id=company_context.company_id)
    await record_audit(
        audit_repository,
        "subscription_canceled",
        user_id=current_user.id,
        company_id=company_context.company_id,
    )
    return await _build_response(
        subscription,
        membership_repository=membership_repository,
        connection_repository=connection_repository,
        company_id=company_context.company_id,
    )
