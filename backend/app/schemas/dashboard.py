from datetime import datetime

from pydantic import BaseModel

from app.domain.dashboard.kpi_registry import KPIMetric, KPIUnit


class MonthlyBreakdownResponse(BaseModel):
    year: int
    month: int
    revenue_cents: int
    expense_cents: int
    profit_cents: int


class CategoryBreakdownResponse(BaseModel):
    category_id: str
    category_name: str
    total_cents: int


class PeriodComparisonResponse(BaseModel):
    revenue_change_pct: float | None
    expense_change_pct: float | None
    profit_change_pct: float | None


class ComputedKPIResponse(BaseModel):
    key: str
    name: str
    description: str
    metric: KPIMetric
    unit: KPIUnit
    value: float


class DashboardSummaryResponse(BaseModel):
    start: datetime
    end: datetime
    revenue_cents: int
    expense_cents: int
    profit_cents: int
    profit_margin_pct: float | None
    average_ticket_cents: int
    transaction_count: int
    active_clients: int
    monthly_breakdown: list[MonthlyBreakdownResponse]
    top_income_categories: list[CategoryBreakdownResponse]
    top_expense_categories: list[CategoryBreakdownResponse]
    comparison: PeriodComparisonResponse
    kpis: list[ComputedKPIResponse]
