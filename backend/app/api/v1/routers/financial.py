from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.v1.deps import (
    get_client_repository,
    get_company_blueprint_repository,
    get_company_context,
    get_current_user,
    get_financial_category_repository,
    get_financial_transaction_repository,
    require_role,
)
from app.application.financial.cancel_transaction import CancelTransactionUseCase
from app.application.financial.create_category import CreateFinancialCategoryUseCase
from app.application.financial.create_transaction import CreateFinancialTransactionUseCase
from app.application.financial.get_cash_flow_summary import GetCashFlowSummaryUseCase
from app.application.financial.import_transactions import (
    ImportRow,
    ImportTransactionsUseCase,
)
from app.application.financial.mark_transaction_paid import MarkTransactionPaidUseCase
from app.application.financial.seed_categories_from_blueprint import (
    SeedFinancialCategoriesFromBlueprintUseCase,
)
from app.application.financial.update_category import UpdateFinancialCategoryUseCase
from app.core.audit import audit_event
from app.core.exceptions import NotFoundError
from app.core.tenant import CompanyContext
from app.domain.blueprint.repository import CompanyBlueprintRepository
from app.domain.client.repository import ClientRepository
from app.domain.company.roles import CompanyRole
from app.domain.financial.entities import (
    CashFlowSummary,
    FinancialCategory,
    FinancialCategoryType,
    FinancialTransaction,
    TransactionStatus,
)
from app.domain.financial.repository import (
    FinancialCategoryRepository,
    FinancialTransactionRepository,
)
from app.domain.user.entities import User
from app.schemas.financial import (
    CashFlowSummaryResponse,
    CreateCategoryRequest,
    CreateTransactionRequest,
    FinancialCategoryResponse,
    FinancialTransactionResponse,
    ImportTransactionsRequest,
    ImportTransactionsResponse,
    MarkPaidRequest,
    UpdateCategoryRequest,
    UpdateTransactionRequest,
)

router = APIRouter(prefix="/companies/{company_id}", tags=["financial"])

_STAFF_ROLES = (
    CompanyRole.OWNER,
    CompanyRole.ADMIN,
    CompanyRole.MANAGER,
    CompanyRole.EMPLOYEE,
)
_MANAGEMENT_ROLES = (CompanyRole.OWNER, CompanyRole.ADMIN, CompanyRole.MANAGER)
_ADMIN_ROLES = (CompanyRole.OWNER, CompanyRole.ADMIN)


def _category_to_response(category: FinancialCategory) -> FinancialCategoryResponse:
    return FinancialCategoryResponse(
        id=category.id,
        company_id=category.company_id,
        name=category.name,
        type=category.type,
        is_active=category.is_active,
        created_at=category.created_at,
    )


def _transaction_to_response(transaction: FinancialTransaction) -> FinancialTransactionResponse:
    return FinancialTransactionResponse(
        id=transaction.id,
        company_id=transaction.company_id,
        category_id=transaction.category_id,
        type=transaction.type,
        amount_cents=transaction.amount_cents,
        description=transaction.description,
        status=transaction.status,
        due_date=transaction.due_date,
        paid_at=transaction.paid_at,
        notes=transaction.notes,
        client_id=transaction.client_id,
        created_by=transaction.created_by,
        created_at=transaction.created_at,
        updated_at=transaction.updated_at,
    )


def _cash_flow_to_response(summary: CashFlowSummary) -> CashFlowSummaryResponse:
    return CashFlowSummaryResponse(
        start=summary.start,
        end=summary.end,
        income_cents=summary.income_cents,
        expense_cents=summary.expense_cents,
        balance_cents=summary.balance_cents,
    )


@router.post(
    "/financial-categories",
    response_model=FinancialCategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_category(
    payload: CreateCategoryRequest,
    company_context: Annotated[CompanyContext, Depends(require_role(*_MANAGEMENT_ROLES))],
    category_repository: Annotated[
        FinancialCategoryRepository, Depends(get_financial_category_repository)
    ],
) -> FinancialCategoryResponse:
    use_case = CreateFinancialCategoryUseCase(category_repository)
    category = await use_case.execute(name=payload.name, type=payload.type)
    return _category_to_response(category)


@router.get("/financial-categories", response_model=list[FinancialCategoryResponse])
async def list_categories(
    company_context: Annotated[CompanyContext, Depends(get_company_context)],
    category_repository: Annotated[
        FinancialCategoryRepository, Depends(get_financial_category_repository)
    ],
    only_active: Annotated[bool, Query()] = True,
) -> list[FinancialCategoryResponse]:
    categories = await category_repository.list_all(only_active=only_active)
    return [_category_to_response(category) for category in categories]


@router.patch("/financial-categories/{category_id}", response_model=FinancialCategoryResponse)
async def update_category(
    category_id: str,
    payload: UpdateCategoryRequest,
    company_context: Annotated[CompanyContext, Depends(require_role(*_MANAGEMENT_ROLES))],
    category_repository: Annotated[
        FinancialCategoryRepository, Depends(get_financial_category_repository)
    ],
) -> FinancialCategoryResponse:
    use_case = UpdateFinancialCategoryUseCase(category_repository)
    category = await use_case.execute(
        category_id=category_id, **payload.model_dump(exclude_unset=True)
    )
    return _category_to_response(category)


@router.post(
    "/financial-categories/seed-from-blueprint",
    response_model=list[FinancialCategoryResponse],
    status_code=status.HTTP_201_CREATED,
)
async def seed_categories_from_blueprint(
    company_context: Annotated[CompanyContext, Depends(require_role(*_ADMIN_ROLES))],
    blueprint_repository: Annotated[
        CompanyBlueprintRepository, Depends(get_company_blueprint_repository)
    ],
    category_repository: Annotated[
        FinancialCategoryRepository, Depends(get_financial_category_repository)
    ],
) -> list[FinancialCategoryResponse]:
    use_case = SeedFinancialCategoriesFromBlueprintUseCase(
        blueprint_repository, category_repository
    )
    created = await use_case.execute(company_id=company_context.company_id)
    return [_category_to_response(category) for category in created]


@router.post(
    "/transactions",
    response_model=FinancialTransactionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_transaction(
    payload: CreateTransactionRequest,
    company_context: Annotated[CompanyContext, Depends(require_role(*_STAFF_ROLES))],
    current_user: Annotated[User, Depends(get_current_user)],
    category_repository: Annotated[
        FinancialCategoryRepository, Depends(get_financial_category_repository)
    ],
    transaction_repository: Annotated[
        FinancialTransactionRepository, Depends(get_financial_transaction_repository)
    ],
    client_repository: Annotated[ClientRepository, Depends(get_client_repository)],
) -> FinancialTransactionResponse:
    use_case = CreateFinancialTransactionUseCase(
        category_repository, transaction_repository, client_repository
    )
    transaction = await use_case.execute(
        category_id=payload.category_id,
        type=payload.type,
        amount_cents=payload.amount_cents,
        description=payload.description,
        due_date=payload.due_date,
        paid_at=payload.paid_at,
        notes=payload.notes,
        client_id=payload.client_id,
        created_by=current_user.id,
    )
    audit_event(
        "transaction_created",
        user_id=current_user.id,
        company_id=company_context.company_id,
        transaction_id=transaction.id,
        type=transaction.type.value,
        amount_cents=transaction.amount_cents,
    )
    return _transaction_to_response(transaction)


@router.post("/transactions/import", response_model=ImportTransactionsResponse)
async def import_transactions(
    payload: ImportTransactionsRequest,
    company_context: Annotated[CompanyContext, Depends(require_role(*_STAFF_ROLES))],
    current_user: Annotated[User, Depends(get_current_user)],
    category_repository: Annotated[
        FinancialCategoryRepository, Depends(get_financial_category_repository)
    ],
    transaction_repository: Annotated[
        FinancialTransactionRepository, Depends(get_financial_transaction_repository)
    ],
) -> ImportTransactionsResponse:
    use_case = ImportTransactionsUseCase(category_repository, transaction_repository)
    result = await use_case.execute(
        rows=[
            ImportRow(
                date=row.date,
                description=row.description,
                amount_cents=row.amount_cents,
                category_name=row.category_name,
                paid=row.paid,
            )
            for row in payload.rows
        ],
        created_by=current_user.id,
    )
    audit_event(
        "transactions_imported",
        user_id=current_user.id,
        company_id=company_context.company_id,
        imported=result.imported,
        categories_created=result.categories_created,
    )
    return ImportTransactionsResponse(
        imported=result.imported, categories_created=result.categories_created
    )


@router.get("/transactions", response_model=list[FinancialTransactionResponse])
async def list_transactions(
    company_context: Annotated[CompanyContext, Depends(get_company_context)],
    transaction_repository: Annotated[
        FinancialTransactionRepository, Depends(get_financial_transaction_repository)
    ],
    type_filter: Annotated[FinancialCategoryType | None, Query(alias="type")] = None,
    status_filter: Annotated[TransactionStatus | None, Query(alias="status")] = None,
) -> list[FinancialTransactionResponse]:
    transactions = await transaction_repository.list_all(type=type_filter, status=status_filter)
    return [_transaction_to_response(transaction) for transaction in transactions]


@router.patch("/transactions/{transaction_id}", response_model=FinancialTransactionResponse)
async def update_transaction(
    transaction_id: str,
    payload: UpdateTransactionRequest,
    company_context: Annotated[CompanyContext, Depends(require_role(*_STAFF_ROLES))],
    transaction_repository: Annotated[
        FinancialTransactionRepository, Depends(get_financial_transaction_repository)
    ],
) -> FinancialTransactionResponse:
    fields = payload.model_dump(exclude_unset=True)
    transaction = await transaction_repository.update(transaction_id, **fields)
    if transaction is None:
        raise NotFoundError("Lançamento não encontrado.")
    return _transaction_to_response(transaction)


@router.post(
    "/transactions/{transaction_id}/mark-paid", response_model=FinancialTransactionResponse
)
async def mark_transaction_paid(
    transaction_id: str,
    payload: MarkPaidRequest,
    company_context: Annotated[CompanyContext, Depends(require_role(*_STAFF_ROLES))],
    transaction_repository: Annotated[
        FinancialTransactionRepository, Depends(get_financial_transaction_repository)
    ],
) -> FinancialTransactionResponse:
    use_case = MarkTransactionPaidUseCase(transaction_repository)
    transaction = await use_case.execute(transaction_id=transaction_id, paid_at=payload.paid_at)
    audit_event(
        "transaction_marked_paid",
        company_id=company_context.company_id,
        transaction_id=transaction.id,
        amount_cents=transaction.amount_cents,
    )
    return _transaction_to_response(transaction)


@router.post("/transactions/{transaction_id}/cancel", response_model=FinancialTransactionResponse)
async def cancel_transaction(
    transaction_id: str,
    company_context: Annotated[CompanyContext, Depends(require_role(*_STAFF_ROLES))],
    transaction_repository: Annotated[
        FinancialTransactionRepository, Depends(get_financial_transaction_repository)
    ],
) -> FinancialTransactionResponse:
    use_case = CancelTransactionUseCase(transaction_repository)
    transaction = await use_case.execute(transaction_id=transaction_id)
    audit_event(
        "transaction_cancelled",
        company_id=company_context.company_id,
        transaction_id=transaction.id,
        amount_cents=transaction.amount_cents,
    )
    return _transaction_to_response(transaction)


@router.get("/cash-flow", response_model=CashFlowSummaryResponse)
async def get_cash_flow_summary(
    start: datetime,
    end: datetime,
    company_context: Annotated[CompanyContext, Depends(get_company_context)],
    transaction_repository: Annotated[
        FinancialTransactionRepository, Depends(get_financial_transaction_repository)
    ],
) -> CashFlowSummaryResponse:
    use_case = GetCashFlowSummaryUseCase(transaction_repository)
    summary = await use_case.execute(start=start, end=end)
    return _cash_flow_to_response(summary)
