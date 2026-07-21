from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.v1.deps import (
    get_company_context,
    get_current_user,
    get_financial_transaction_repository,
    get_recurring_repository,
    require_role,
)
from app.application.recurring.generate_due import GenerateDueRecurringUseCase
from app.core.exceptions import NotFoundError
from app.core.tenant import CompanyContext
from app.domain.company.roles import CompanyRole
from app.domain.financial.repository import FinancialTransactionRepository
from app.domain.recurring.entities import RecurringTransaction
from app.domain.recurring.repository import RecurringTransactionRepository
from app.domain.user.entities import User
from app.schemas.recurring import (
    CreateRecurringRequest,
    GenerateRecurringResponse,
    RecurringResponse,
    UpdateRecurringRequest,
)

router = APIRouter(prefix="/companies/{company_id}/recurring", tags=["recurring"])

_MANAGEMENT_ROLES = (CompanyRole.OWNER, CompanyRole.ADMIN, CompanyRole.MANAGER)


def _to_response(item: RecurringTransaction) -> RecurringResponse:
    return RecurringResponse(
        id=item.id,
        category_id=item.category_id,
        type=item.type,
        amount_cents=item.amount_cents,
        description=item.description,
        frequency=item.frequency,
        anchor_day=item.anchor_day,
        next_run_date=item.next_run_date,
        active=item.active,
        notes=item.notes,
        client_id=item.client_id,
        last_run_at=item.last_run_at,
    )


@router.get("", response_model=list[RecurringResponse])
async def list_recurring(
    company_context: Annotated[CompanyContext, Depends(get_company_context)],
    repository: Annotated[RecurringTransactionRepository, Depends(get_recurring_repository)],
) -> list[RecurringResponse]:
    items = await repository.list_all()
    return [_to_response(item) for item in items]


@router.post("", response_model=RecurringResponse, status_code=status.HTTP_201_CREATED)
async def create_recurring(
    payload: CreateRecurringRequest,
    company_context: Annotated[CompanyContext, Depends(require_role(*_MANAGEMENT_ROLES))],
    current_user: Annotated[User, Depends(get_current_user)],
    repository: Annotated[RecurringTransactionRepository, Depends(get_recurring_repository)],
) -> RecurringResponse:
    item = await repository.create(
        category_id=payload.category_id,
        type=payload.type,
        amount_cents=payload.amount_cents,
        description=payload.description.strip(),
        frequency=payload.frequency,
        anchor_day=payload.start_date.day,
        next_run_date=payload.start_date,
        notes=payload.notes.strip() if payload.notes else None,
        client_id=payload.client_id,
        created_by=current_user.id,
    )
    return _to_response(item)


@router.put("/{recurring_id}", response_model=RecurringResponse)
async def update_recurring(
    recurring_id: str,
    payload: UpdateRecurringRequest,
    company_context: Annotated[CompanyContext, Depends(require_role(*_MANAGEMENT_ROLES))],
    repository: Annotated[RecurringTransactionRepository, Depends(get_recurring_repository)],
) -> RecurringResponse:
    fields = payload.model_dump(exclude_unset=True, exclude_none=True)
    # Mudar a próxima data reancora o dia do mês (ex.: passar a vencer todo dia 5).
    if "next_run_date" in fields:
        fields["anchor_day"] = payload.next_run_date.day  # type: ignore[union-attr]
    updated = await repository.update(recurring_id, **fields)
    if updated is None:
        raise NotFoundError("Recorrência não encontrada.")
    return _to_response(updated)


@router.delete("/{recurring_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recurring(
    recurring_id: str,
    company_context: Annotated[CompanyContext, Depends(require_role(*_MANAGEMENT_ROLES))],
    repository: Annotated[RecurringTransactionRepository, Depends(get_recurring_repository)],
) -> None:
    deleted = await repository.delete(recurring_id)
    if not deleted:
        raise NotFoundError("Recorrência não encontrada.")


@router.post("/run", response_model=GenerateRecurringResponse)
async def run_recurring(
    company_context: Annotated[CompanyContext, Depends(require_role(*_MANAGEMENT_ROLES))],
    current_user: Annotated[User, Depends(get_current_user)],
    repository: Annotated[RecurringTransactionRepository, Depends(get_recurring_repository)],
    transaction_repository: Annotated[
        FinancialTransactionRepository, Depends(get_financial_transaction_repository)
    ],
) -> GenerateRecurringResponse:
    use_case = GenerateDueRecurringUseCase(repository, transaction_repository)
    result = await use_case.execute(as_of=datetime.now(UTC), created_by=current_user.id)
    return GenerateRecurringResponse(created=result.created)
