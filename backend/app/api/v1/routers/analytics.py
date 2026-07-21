from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.v1.deps import get_company_context, get_platform_sale_repository
from app.application.platform_sales.analytics import GetSalesAnalyticsUseCase
from app.core.tenant import CompanyContext
from app.domain.platform_sales.entities import SalesAnalytics
from app.domain.platform_sales.repository import PlatformSaleRepository
from app.schemas.analytics import (
    PeakHourResponse,
    PlatformMetricResponse,
    SalesAnalyticsResponse,
    TopProductResponse,
)

router = APIRouter(prefix="/companies/{company_id}/analytics", tags=["analytics"])


def _to_response(analytics: SalesAnalytics) -> SalesAnalyticsResponse:
    return SalesAnalyticsResponse(
        total_gross_cents=analytics.total_gross_cents,
        total_refunds_cents=analytics.total_refunds_cents,
        total_net_cents=analytics.total_net_cents,
        total_orders=analytics.total_orders,
        total_refunds=analytics.total_refunds,
        avg_ticket_cents=analytics.avg_ticket_cents,
        unique_buyers=analytics.unique_buyers,
        by_platform=[
            PlatformMetricResponse(
                provider=m.provider,
                gross_cents=m.gross_cents,
                refunds_cents=m.refunds_cents,
                net_cents=m.net_cents,
                orders=m.orders,
                refunds=m.refunds,
                avg_ticket_cents=m.avg_ticket_cents,
            )
            for m in analytics.by_platform
        ],
        top_products=[
            TopProductResponse(
                product=p.product, quantity=p.quantity, revenue_cents=p.revenue_cents
            )
            for p in analytics.top_products
        ],
        peak_hours=[PeakHourResponse(hour=h.hour, orders=h.orders) for h in analytics.peak_hours],
    )


@router.get("/sales", response_model=SalesAnalyticsResponse)
async def sales_analytics(
    company_context: Annotated[CompanyContext, Depends(get_company_context)],
    platform_sale_repository: Annotated[
        PlatformSaleRepository, Depends(get_platform_sale_repository)
    ],
    days: Annotated[int, Query(ge=1, le=365)] = 30,
) -> SalesAnalyticsResponse:
    use_case = GetSalesAnalyticsUseCase(platform_sale_repository)
    analytics = await use_case.execute(days=days)
    return _to_response(analytics)
