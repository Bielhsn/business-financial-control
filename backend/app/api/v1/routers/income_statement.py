from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.v1.deps import (
    get_company_context,
    get_financial_category_repository,
    get_financial_transaction_repository,
)
from app.application.financial.income_statement import (
    GetIncomeStatementUseCase,
    IncomeStatement,
    IncomeStatementComparison,
)
from app.core.tenant import CompanyContext
from app.domain.financial.repository import (
    FinancialCategoryRepository,
    FinancialTransactionRepository,
)
from app.schemas.income_statement import (
    IncomeStatementComparisonResponse,
    IncomeStatementResponse,
    StatementLineResponse,
)

router = APIRouter(prefix="/companies/{company_id}/income-statement", tags=["income-statement"])


def _to_statement_response(statement: IncomeStatement) -> IncomeStatementResponse:
    return IncomeStatementResponse(
        income_lines=[
            StatementLineResponse(
                category_id=line.category_id,
                category_name=line.category_name,
                amount_cents=line.amount_cents,
            )
            for line in statement.income_lines
        ],
        expense_lines=[
            StatementLineResponse(
                category_id=line.category_id,
                category_name=line.category_name,
                amount_cents=line.amount_cents,
            )
            for line in statement.expense_lines
        ],
        total_income_cents=statement.total_income_cents,
        total_expense_cents=statement.total_expense_cents,
        net_result_cents=statement.net_result_cents,
    )


def _to_response(comparison: IncomeStatementComparison) -> IncomeStatementComparisonResponse:
    return IncomeStatementComparisonResponse(
        year=comparison.year,
        month=comparison.month,
        current=_to_statement_response(comparison.current),
        previous_income_cents=comparison.previous_income_cents,
        previous_expense_cents=comparison.previous_expense_cents,
        previous_net_result_cents=comparison.previous_net_result_cents,
        income_change_pct=comparison.income_change_pct,
        expense_change_pct=comparison.expense_change_pct,
        net_change_pct=comparison.net_change_pct,
    )


@router.get("", response_model=IncomeStatementComparisonResponse)
async def get_income_statement(
    company_context: Annotated[CompanyContext, Depends(get_company_context)],
    transaction_repository: Annotated[
        FinancialTransactionRepository, Depends(get_financial_transaction_repository)
    ],
    category_repository: Annotated[
        FinancialCategoryRepository, Depends(get_financial_category_repository)
    ],
    year: Annotated[int | None, Query(ge=2000, le=2100)] = None,
    month: Annotated[int | None, Query(ge=1, le=12)] = None,
) -> IncomeStatementComparisonResponse:
    now = datetime.now(UTC)
    use_case = GetIncomeStatementUseCase(transaction_repository, category_repository)
    comparison = await use_case.execute(year=year or now.year, month=month or now.month)
    return _to_response(comparison)
