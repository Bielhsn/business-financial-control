from pydantic import BaseModel


class PlatformMetricResponse(BaseModel):
    provider: str
    gross_cents: int
    refunds_cents: int
    net_cents: int
    orders: int
    refunds: int
    avg_ticket_cents: int


class TopProductResponse(BaseModel):
    product: str
    quantity: int
    revenue_cents: int


class PeakHourResponse(BaseModel):
    hour: int
    orders: int


class SalesAnalyticsResponse(BaseModel):
    total_gross_cents: int
    total_refunds_cents: int
    total_net_cents: int
    total_orders: int
    total_refunds: int
    avg_ticket_cents: int
    unique_buyers: int
    by_platform: list[PlatformMetricResponse]
    top_products: list[TopProductResponse]
    peak_hours: list[PeakHourResponse]


class MonthPointResponse(BaseModel):
    year: int
    month: int
    income_cents: int
    expense_cents: int
    net_cents: int


class CashflowForecastResponse(BaseModel):
    current_month_actual_net_cents: int
    current_month_projected_net_cents: int
    next_month_projected_net_cents: int
    trend_pct: float | None
    method: str
    history: list[MonthPointResponse]
