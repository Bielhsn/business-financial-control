from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.v1.deps import (
    get_company_context,
    get_financial_transaction_repository,
    get_goal_repository,
    require_role,
)
from app.application.goals.progress import GetGoalsProgressUseCase, GoalProgress
from app.core.tenant import CompanyContext
from app.domain.company.roles import CompanyRole
from app.domain.financial.repository import FinancialTransactionRepository
from app.domain.goals.entities import GoalMetric
from app.domain.goals.repository import GoalRepository
from app.schemas.goal import GoalProgressResponse, SetGoalRequest

router = APIRouter(prefix="/companies/{company_id}/goals", tags=["goals"])

_MANAGEMENT_ROLES = (CompanyRole.OWNER, CompanyRole.ADMIN, CompanyRole.MANAGER)


def _to_response(progress: GoalProgress) -> GoalProgressResponse:
    return GoalProgressResponse(
        metric=progress.metric,
        target_cents=progress.target_cents,
        actual_cents=progress.actual_cents,
        projected_cents=progress.projected_cents,
        progress_pct=progress.progress_pct,
        on_track=progress.on_track,
    )


@router.get("", response_model=list[GoalProgressResponse])
async def list_goals(
    company_context: Annotated[CompanyContext, Depends(get_company_context)],
    goal_repository: Annotated[GoalRepository, Depends(get_goal_repository)],
    transaction_repository: Annotated[
        FinancialTransactionRepository, Depends(get_financial_transaction_repository)
    ],
) -> list[GoalProgressResponse]:
    use_case = GetGoalsProgressUseCase(goal_repository, transaction_repository)
    progress = await use_case.execute()
    return [_to_response(item) for item in progress]


@router.put("/{metric}", response_model=list[GoalProgressResponse])
async def set_goal(
    metric: GoalMetric,
    payload: SetGoalRequest,
    company_context: Annotated[CompanyContext, Depends(require_role(*_MANAGEMENT_ROLES))],
    goal_repository: Annotated[GoalRepository, Depends(get_goal_repository)],
    transaction_repository: Annotated[
        FinancialTransactionRepository, Depends(get_financial_transaction_repository)
    ],
) -> list[GoalProgressResponse]:
    await goal_repository.set(metric=metric, target_cents=payload.target_cents)
    use_case = GetGoalsProgressUseCase(goal_repository, transaction_repository)
    progress = await use_case.execute()
    return [_to_response(item) for item in progress]


@router.delete("/{metric}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_goal(
    metric: GoalMetric,
    company_context: Annotated[CompanyContext, Depends(require_role(*_MANAGEMENT_ROLES))],
    goal_repository: Annotated[GoalRepository, Depends(get_goal_repository)],
) -> None:
    await goal_repository.delete(metric)
