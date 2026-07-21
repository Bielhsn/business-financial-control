from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.v1.deps import (
    get_company_context,
    get_company_membership_repository,
    get_connection_repository,
    get_financial_transaction_repository,
    get_goal_repository,
    get_platform_sale_repository,
    get_subscription_repository,
)
from app.application.alerts.use_case import GetAlertsUseCase
from app.core.tenant import CompanyContext
from app.domain.company.repository import CompanyMembershipRepository
from app.domain.connector.repository import ConnectionRepository
from app.domain.financial.repository import FinancialTransactionRepository
from app.domain.goals.repository import GoalRepository
from app.domain.platform_sales.repository import PlatformSaleRepository
from app.domain.subscription.repository import SubscriptionRepository
from app.schemas.alert import AlertResponse

router = APIRouter(prefix="/companies/{company_id}/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertResponse])
async def list_alerts(
    company_context: Annotated[CompanyContext, Depends(get_company_context)],
    connection_repository: Annotated[ConnectionRepository, Depends(get_connection_repository)],
    goal_repository: Annotated[GoalRepository, Depends(get_goal_repository)],
    transaction_repository: Annotated[
        FinancialTransactionRepository, Depends(get_financial_transaction_repository)
    ],
    platform_sale_repository: Annotated[
        PlatformSaleRepository, Depends(get_platform_sale_repository)
    ],
    subscription_repository: Annotated[
        SubscriptionRepository, Depends(get_subscription_repository)
    ],
    membership_repository: Annotated[
        CompanyMembershipRepository, Depends(get_company_membership_repository)
    ],
) -> list[AlertResponse]:
    use_case = GetAlertsUseCase(
        connection_repository=connection_repository,
        goal_repository=goal_repository,
        transaction_repository=transaction_repository,
        platform_sale_repository=platform_sale_repository,
        subscription_repository=subscription_repository,
        membership_repository=membership_repository,
    )
    alerts = await use_case.execute(company_id=company_context.company_id)
    return [
        AlertResponse(
            code=alert.code,
            severity=alert.severity,
            title=alert.title,
            message=alert.message,
            action=alert.action,
        )
        for alert in alerts
    ]
