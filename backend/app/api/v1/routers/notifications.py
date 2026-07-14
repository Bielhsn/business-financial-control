from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.v1.deps import get_company_context, get_financial_transaction_repository
from app.application.notifications.get_notifications import GetNotificationsUseCase
from app.core.tenant import CompanyContext
from app.domain.financial.repository import FinancialTransactionRepository
from app.schemas.notifications import NotificationResponse

router = APIRouter(prefix="/companies/{company_id}/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationResponse])
async def list_notifications(
    company_context: Annotated[CompanyContext, Depends(get_company_context)],
    transaction_repository: Annotated[
        FinancialTransactionRepository, Depends(get_financial_transaction_repository)
    ],
) -> list[NotificationResponse]:
    notifications = await GetNotificationsUseCase(transaction_repository).execute()
    return [
        NotificationResponse(
            kind=item.kind,
            transaction_id=item.transaction_id,
            description=item.description,
            amount_cents=item.amount_cents,
            type=item.type,
            due_date=item.due_date,
        )
        for item in notifications
    ]
