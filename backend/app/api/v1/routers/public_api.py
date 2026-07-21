import calendar
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.v1.deps import (
    get_api_key_company,
    get_connection_repository,
    get_financial_transaction_repository,
    get_goal_repository,
    get_platform_sale_repository,
)
from app.application.health.use_case import GetHealthScoreUseCase
from app.domain.connector.repository import ConnectionRepository
from app.domain.financial.entities import FinancialCategoryType
from app.domain.financial.repository import FinancialTransactionRepository
from app.domain.goals.repository import GoalRepository
from app.domain.platform_sales.repository import PlatformSaleRepository
from app.schemas.api_key import PublicSummaryResponse

# API pública, autenticada por X-API-Key (não por sessão de usuário).
router = APIRouter(prefix="/public/v1", tags=["public-api"])


@router.get("/summary", response_model=PublicSummaryResponse)
async def public_summary(
    company_id: Annotated[str, Depends(get_api_key_company)],
    transaction_repository: Annotated[
        FinancialTransactionRepository, Depends(get_financial_transaction_repository)
    ],
    platform_sale_repository: Annotated[
        PlatformSaleRepository, Depends(get_platform_sale_repository)
    ],
    goal_repository: Annotated[GoalRepository, Depends(get_goal_repository)],
    connection_repository: Annotated[ConnectionRepository, Depends(get_connection_repository)],
) -> PublicSummaryResponse:
    now = datetime.now(UTC)
    month_start = datetime(now.year, now.month, 1, tzinfo=UTC)
    month_end = datetime(
        now.year, now.month, calendar.monthrange(now.year, now.month)[1], 23, 59, 59, tzinfo=UTC
    )
    month_tx = await transaction_repository.list_paid_between(start=month_start, end=month_end)
    income = sum(t.amount_cents for t in month_tx if t.type == FinancialCategoryType.INCOME)
    expense = sum(t.amount_cents for t in month_tx if t.type == FinancialCategoryType.EXPENSE)

    health = await GetHealthScoreUseCase(
        transaction_repository=transaction_repository,
        platform_sale_repository=platform_sale_repository,
        goal_repository=goal_repository,
        connection_repository=connection_repository,
    ).execute(now=now)

    return PublicSummaryResponse(
        company_id=company_id,
        month_income_cents=income,
        month_expense_cents=expense,
        month_net_cents=income - expense,
        health_score=health.score,
        health_rating=health.rating.value,
    )
