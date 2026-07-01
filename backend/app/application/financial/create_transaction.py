from datetime import datetime

from app.core.exceptions import NotFoundError, ValidationError
from app.domain.financial.entities import (
    FinancialCategoryType,
    FinancialTransaction,
    TransactionStatus,
)
from app.domain.financial.repository import (
    FinancialCategoryRepository,
    FinancialTransactionRepository,
)


class CreateFinancialTransactionUseCase:
    def __init__(
        self,
        category_repository: FinancialCategoryRepository,
        transaction_repository: FinancialTransactionRepository,
    ) -> None:
        self._category_repository = category_repository
        self._transaction_repository = transaction_repository

    async def execute(
        self,
        *,
        category_id: str,
        type: FinancialCategoryType,
        amount_cents: int,
        description: str,
        due_date: datetime | None,
        paid_at: datetime | None,
        notes: str | None,
        created_by: str,
    ) -> FinancialTransaction:
        category = await self._category_repository.get_by_id(category_id)
        if category is None or not category.is_active:
            raise NotFoundError("Categoria financeira não encontrada.")
        if category.type != type:
            raise ValidationError("O tipo do lançamento não corresponde ao tipo da categoria.")
        if amount_cents <= 0:
            raise ValidationError("O valor do lançamento deve ser maior que zero.")

        status = TransactionStatus.PAID if paid_at is not None else TransactionStatus.PENDING

        return await self._transaction_repository.create(
            category_id=category_id,
            type=type,
            amount_cents=amount_cents,
            description=description.strip(),
            status=status,
            due_date=due_date,
            paid_at=paid_at,
            notes=notes.strip() if notes else None,
            created_by=created_by,
        )
