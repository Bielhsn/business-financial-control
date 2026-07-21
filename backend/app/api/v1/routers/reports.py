from typing import Annotated

from fastapi import APIRouter, Depends, Response

from app.api.v1.deps import (
    get_company_context,
    get_financial_category_repository,
    get_financial_transaction_repository,
    get_platform_sale_repository,
)
from app.application.reports.csv_export import (
    financial_transactions_csv,
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
