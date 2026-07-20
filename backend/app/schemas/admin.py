from pydantic import BaseModel

from app.domain.subscription.plans import PlanTier


class RevenueMetricsResponse(BaseModel):
    mrr_cents: int
    arr_cents: int
    active_paying: int
    trials: int
    platform_gmv_cents: int
    platform_expenses_cents: int


class CustomerMetricsResponse(BaseModel):
    total_companies: int
    active_companies: int
    inactive_companies: int
    new_this_month: int
    churned: int
    churn_rate_pct: float


class SegmentMetricResponse(BaseModel):
    segment: str
    company_count: int


class PlanBreakdownResponse(BaseModel):
    tier: PlanTier
    subscribers: int
    mrr_cents: int


class SubscriptionMetricsResponse(BaseModel):
    by_status: dict[str, int]
    by_plan: list[PlanBreakdownResponse]
    past_due: int


class SystemMetricsResponse(BaseModel):
    total_users: int
    total_companies: int
    total_connections: int
    connections_with_error: int


class AdminOverviewResponse(BaseModel):
    revenue: RevenueMetricsResponse
    customers: CustomerMetricsResponse
    segments: list[SegmentMetricResponse]
    subscriptions: SubscriptionMetricsResponse
    system: SystemMetricsResponse


class PlatformAdminStatusResponse(BaseModel):
    is_platform_admin: bool
