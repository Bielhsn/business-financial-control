from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.v1.deps import get_company_context, get_financial_transaction_repository
from app.application.financial.accounts import (
    AccountsBucket,
    AccountsSummary,
    GetAccountsUseCase,
)
from app.core.tenant import CompanyContext
from app.domain.financial.repository import FinancialTransactionRepository
from app.schemas.accounts import (
    AccountItemResponse,
    AccountsBucketResponse,
    AccountsSummaryResponse,
)

router = APIRouter(prefix="/companies/{company_id}/accounts", tags=["accounts"])


def _to_bucket_response(bucket: AccountsBucket) -> AccountsBucketResponse:
    return AccountsBucketResponse(
        overdue_cents=bucket.overdue_cents,
        due_soon_cents=bucket.due_soon_cents,
        upcoming_cents=bucket.upcoming_cents,
        total_cents=bucket.total_cents,
        items=[
            AccountItemResponse(
                id=item.id,
                description=item.description,
                amount_cents=item.amount_cents,
                due_date=item.due_date,
                category_id=item.category_id,
                days_until_due=item.days_until_due,
                is_overdue=item.is_overdue,
            )
            for item in bucket.items
        ],
    )


def _to_response(summary: AccountsSummary) -> AccountsSummaryResponse:
    return AccountsSummaryResponse(
        payable=_to_bucket_response(summary.payable),
        receivable=_to_bucket_response(summary.receivable),
    )


@router.get("", response_model=AccountsSummaryResponse)
async def get_accounts(
    company_context: Annotated[CompanyContext, Depends(get_company_context)],
    transaction_repository: Annotated[
        FinancialTransactionRepository, Depends(get_financial_transaction_repository)
    ],
) -> AccountsSummaryResponse:
    summary = await GetAccountsUseCase(transaction_repository).execute(today=datetime.now(UTC))
    return _to_response(summary)
