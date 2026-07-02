from dataclasses import dataclass
from datetime import datetime

from app.domain.dashboard.kpi_registry import KPIMetric, KPIUnit


@dataclass
class MonthlyBreakdown:
    year: int
    month: int
    revenue_cents: int
    expense_cents: int
    profit_cents: int


@dataclass
class CategoryBreakdown:
    category_id: str
    category_name: str
    total_cents: int


@dataclass
class PeriodComparison:
    revenue_change_pct: float | None
    expense_change_pct: float | None
    profit_change_pct: float | None


@dataclass
class ComputedKPI:
    key: str
    name: str
    description: str
    metric: KPIMetric
    unit: KPIUnit
    value: float


@dataclass
class DashboardSummary:
    start: datetime
    end: datetime
    revenue_cents: int
    expense_cents: int
    profit_cents: int
    profit_margin_pct: float | None
    average_ticket_cents: int
    transaction_count: int
    active_clients: int
    monthly_breakdown: list[MonthlyBreakdown]
    top_income_categories: list[CategoryBreakdown]
    top_expense_categories: list[CategoryBreakdown]
    comparison: PeriodComparison
    kpis: list[ComputedKPI]
