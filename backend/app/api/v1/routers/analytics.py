from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.v1.deps import (
    get_company_context,
    get_financial_transaction_repository,
    get_platform_sale_repository,
)
from app.application.forecast.cashflow import GetCashflowForecastUseCase
from app.application.platform_sales.analytics import GetSalesAnalyticsUseCase
from app.core.tenant import CompanyContext
from app.domain.financial.repository import FinancialTransactionRepository
from app.domain.forecast.entities import CashflowForecast
from app.domain.platform_sales.entities import SalesAnalytics
from app.domain.platform_sales.repository import PlatformSaleRepository
from app.schemas.analytics import (
    CashflowForecastResponse,
    MonthPointResponse,
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


def _to_forecast_response(forecast: CashflowForecast) -> CashflowForecastResponse:
    return CashflowForecastResponse(
        current_month_actual_net_cents=forecast.current_month_actual_net_cents,
        current_month_projected_net_cents=forecast.current_month_projected_net_cents,
        next_month_projected_net_cents=forecast.next_month_projected_net_cents,
        trend_pct=forecast.trend_pct,
        method=forecast.method,
        history=[
            MonthPointResponse(
                year=point.year,
                month=point.month,
                income_cents=point.income_cents,
                expense_cents=point.expense_cents,
                net_cents=point.net_cents,
            )
            for point in forecast.history
        ],
    )


@router.get("/forecast", response_model=CashflowForecastResponse)
async def cashflow_forecast(
    company_context: Annotated[CompanyContext, Depends(get_company_context)],
    transaction_repository: Annotated[
        FinancialTransactionRepository, Depends(get_financial_transaction_repository)
    ],
) -> CashflowForecastResponse:
    use_case = GetCashflowForecastUseCase(transaction_repository)
    forecast = await use_case.execute()
    return _to_forecast_response(forecast)
