from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response

from app.api.v1.deps import (
    get_company_context,
    get_financial_category_repository,
    get_financial_transaction_repository,
    get_platform_sale_repository,
)
from app.application.financial.accounts import GetAccountsUseCase
from app.application.financial.income_statement import GetIncomeStatementUseCase
from app.application.reports.csv_export import (
    accounts_csv,
    financial_transactions_csv,
    income_statement_csv,
    platform_sales_csv,
)
from app.core.tenant import CompanyContext
from app.domain.financial.repository import (
    FinancialCategoryRepository,
    FinancialTransactionRepository,
)
from app.domain.platform_sales.repository import PlatformSaleRepository

router = APIRouter(prefix="/companies/{company_id}/reports", tags=["reports"])


def _csv_response(content: str, filename: str) -> Response:
    # BOM (﻿) faz o Excel abrir UTF-8 corretamente (acentos em pt-BR).
    return Response(
        content="﻿" + content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/financial.csv")
async def financial_report(
    company_context: Annotated[CompanyContext, Depends(get_company_context)],
    transaction_repository: Annotated[
        FinancialTransactionRepository, Depends(get_financial_transaction_repository)
    ],
    category_repository: Annotated[
        FinancialCategoryRepository, Depends(get_financial_category_repository)
    ],
) -> Response:
    transactions = await transaction_repository.list_all()
    categories = await category_repository.list_all(only_active=False)
    names = {category.id: category.name for category in categories}
    content = financial_transactions_csv(transactions, category_names=names)
    return _csv_response(content, "lancamentos.csv")


@router.get("/income-statement.csv")
async def income_statement_report(
    company_context: Annotated[CompanyContext, Depends(get_company_context)],
    transaction_repository: Annotated[
        FinancialTransactionRepository, Depends(get_financial_transaction_repository)
    ],
    category_repository: Annotated[
        FinancialCategoryRepository, Depends(get_financial_category_repository)
    ],
    year: Annotated[int | None, Query(ge=2000, le=2100)] = None,
    month: Annotated[int | None, Query(ge=1, le=12)] = None,
) -> Response:
    now = datetime.now(UTC)
    comparison = await GetIncomeStatementUseCase(
        transaction_repository, category_repository
    ).execute(year=year or now.year, month=month or now.month)
    content = income_statement_csv(comparison)
    return _csv_response(content, f"dre-{comparison.year}-{comparison.month:02d}.csv")


@router.get("/accounts.csv")
async def accounts_report(
    company_context: Annotated[CompanyContext, Depends(get_company_context)],
    transaction_repository: Annotated[
        FinancialTransactionRepository, Depends(get_financial_transaction_repository)
    ],
) -> Response:
    summary = await GetAccountsUseCase(transaction_repository).execute(today=datetime.now(UTC))
    content = accounts_csv(summary)
    return _csv_response(content, "contas.csv")


@router.get("/sales.csv")
async def sales_report(
    company_context: Annotated[CompanyContext, Depends(get_company_context)],
    platform_sale_repository: Annotated[
        PlatformSaleRepository, Depends(get_platform_sale_repository)
    ],
) -> Response:
    sales = await platform_sale_repository.list_since(None)
    content = platform_sales_csv(sales)
    return _csv_response(content, "vendas.csv")
