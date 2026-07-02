from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.v1.deps import (
    get_company_blueprint_repository,
    get_company_context,
    get_financial_category_repository,
    get_financial_transaction_repository,
)
from app.application.dashboard.get_dashboard import GetDashboardUseCase
from app.core.tenant import CompanyContext
from app.domain.blueprint.repository import CompanyBlueprintRepository
from app.domain.dashboard.entities import DashboardSummary
from app.domain.financial.repository import (
    FinancialCategoryRepository,
    FinancialTransactionRepository,
)
from app.schemas.dashboard import (
    CategoryBreakdownResponse,
    ComputedKPIResponse,
    DashboardSummaryResponse,
    MonthlyBreakdownResponse,
    PeriodComparisonResponse,
)

router = APIRouter(prefix="/companies/{company_id}/dashboard", tags=["dashboard"])


def _to_response(summary: DashboardSummary) -> DashboardSummaryResponse:
    return DashboardSummaryResponse(
        start=summary.start,
        end=summary.end,
        revenue_cents=summary.revenue_cents,
        expense_cents=summary.expense_cents,
        profit_cents=summary.profit_cents,
        profit_margin_pct=summary.profit_margin_pct,
        average_ticket_cents=summary.average_ticket_cents,
        transaction_count=summary.transaction_count,
        active_clients=summary.active_clients,
        monthly_breakdown=[
            MonthlyBreakdownResponse(
                year=item.year,
                month=item.month,
                revenue_cents=item.revenue_cents,
                expense_cents=item.expense_cents,
                profit_cents=item.profit_cents,
            )
            for item in summary.monthly_breakdown
        ],
        top_income_categories=[
            CategoryBreakdownResponse(
                category_id=item.category_id,
                category_name=item.category_name,
                total_cents=item.total_cents,
            )
            for item in summary.top_income_categories
        ],
        top_expense_categories=[
            CategoryBreakdownResponse(
                category_id=item.category_id,
                category_name=item.category_name,
                total_cents=item.total_cents,
            )
            for item in summary.top_expense_categories
        ],
        comparison=PeriodComparisonResponse(
            revenue_change_pct=summary.comparison.revenue_change_pct,
            expense_change_pct=summary.comparison.expense_change_pct,
            profit_change_pct=summary.comparison.profit_change_pct,
        ),
        kpis=[
            ComputedKPIResponse(
                key=item.key,
                name=item.name,
                description=item.description,
                metric=item.metric,
                unit=item.unit,
                value=item.value,
            )
            for item in summary.kpis
        ],
    )


@router.get("", response_model=DashboardSummaryResponse)
async def get_dashboard(
    start: datetime,
    end: datetime,
    company_context: Annotated[CompanyContext, Depends(get_company_context)],
    transaction_repository: Annotated[
        FinancialTransactionRepository, Depends(get_financial_transaction_repository)
    ],
    category_repository: Annotated[
        FinancialCategoryRepository, Depends(get_financial_category_repository)
    ],
    blueprint_repository: Annotated[
        CompanyBlueprintRepository, Depends(get_company_blueprint_repository)
    ],
    months: Annotated[int, Query(ge=1, le=24)] = 6,
) -> DashboardSummaryResponse:
    use_case = GetDashboardUseCase(
        transaction_repository, category_repository, blueprint_repository
    )
    summary = await use_case.execute(
        company_id=company_context.company_id, start=start, end=end, months=months
    )
    return _to_response(summary)
