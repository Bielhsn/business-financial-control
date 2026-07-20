from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.v1.deps import (
    get_admin_metrics_repository,
    get_current_user,
    get_subscription_repository,
    require_platform_admin,
)
from app.application.admin.overview import GetAdminOverviewUseCase
from app.core.config import Settings, get_settings
from app.domain.admin.metrics import AdminOverview
from app.domain.admin.repository import AdminMetricsRepository
from app.domain.subscription.repository import SubscriptionRepository
from app.domain.user.entities import User
from app.schemas.admin import (
    AdminOverviewResponse,
    CustomerMetricsResponse,
    PlanBreakdownResponse,
    PlatformAdminStatusResponse,
    RevenueMetricsResponse,
    SegmentMetricResponse,
    SubscriptionMetricsResponse,
    SystemMetricsResponse,
)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/me", response_model=PlatformAdminStatusResponse)
async def platform_admin_status(
    current_user: Annotated[User, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> PlatformAdminStatusResponse:
    """Diz ao frontend se o usuário logado é super-admin (para exibir o menu)."""
    return PlatformAdminStatusResponse(
        is_platform_admin=settings.is_platform_admin(current_user.email)
    )


def _to_response(overview: AdminOverview) -> AdminOverviewResponse:
    assert overview.subscriptions is not None
    assert overview.system is not None
    return AdminOverviewResponse(
        revenue=RevenueMetricsResponse(
            mrr_cents=overview.revenue.mrr_cents,
            arr_cents=overview.revenue.arr_cents,
            active_paying=overview.revenue.active_paying,
            trials=overview.revenue.trials,
            platform_gmv_cents=overview.revenue.platform_gmv_cents,
            platform_expenses_cents=overview.revenue.platform_expenses_cents,
        ),
        customers=CustomerMetricsResponse(
            total_companies=overview.customers.total_companies,
            active_companies=overview.customers.active_companies,
            inactive_companies=overview.customers.inactive_companies,
            new_this_month=overview.customers.new_this_month,
            churned=overview.customers.churned,
            churn_rate_pct=overview.customers.churn_rate_pct,
        ),
        segments=[
            SegmentMetricResponse(segment=s.segment, company_count=s.company_count)
            for s in overview.segments
        ],
        subscriptions=SubscriptionMetricsResponse(
            by_status={
                status.value: count for status, count in overview.subscriptions.by_status.items()
            },
            by_plan=[
                PlanBreakdownResponse(tier=b.tier, subscribers=b.subscribers, mrr_cents=b.mrr_cents)
                for b in overview.subscriptions.by_plan
            ],
            past_due=overview.subscriptions.past_due,
        ),
        system=SystemMetricsResponse(
            total_users=overview.system.total_users,
            total_companies=overview.system.total_companies,
            total_connections=overview.system.total_connections,
            connections_with_error=overview.system.connections_with_error,
        ),
    )


@router.get("/overview", response_model=AdminOverviewResponse)
async def admin_overview(
    _admin: Annotated[User, Depends(require_platform_admin)],
    admin_metrics_repository: Annotated[
        AdminMetricsRepository, Depends(get_admin_metrics_repository)
    ],
    subscription_repository: Annotated[
        SubscriptionRepository, Depends(get_subscription_repository)
    ],
) -> AdminOverviewResponse:
    use_case = GetAdminOverviewUseCase(admin_metrics_repository, subscription_repository)
    overview = await use_case.execute()
    return _to_response(overview)
