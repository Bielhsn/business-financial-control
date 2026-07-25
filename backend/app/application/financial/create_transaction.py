from datetime import datetime

from app.application.client.visit_tracking import as_utc, is_newer_visit
from app.core.exceptions import NotFoundError, ValidationError
from app.domain.client.entities import Client
from app.domain.client.repository import ClientRepository
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
        client_repository: ClientRepository,
    ) -> None:
        self._category_repository = category_repository
        self._transaction_repository = transaction_repository
        self._client_repository = client_repository

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
        client_id: str | None,
        created_by: str,
    ) -> FinancialTransaction:
        category = await self._category_repository.get_by_id(category_id)
        if category is None or not category.is_active:
            raise NotFoundError("Categoria financeira não encontrada.")
        if category.type != type:
            raise ValidationError("O tipo do lançamento não corresponde ao tipo da categoria.")
        if amount_cents <= 0:
            raise ValidationError("O valor do lançamento deve ser maior que zero.")

        client: Client | None = None
        if client_id is not None:
            client = await self._client_repository.get_by_id(client_id)
            if client is None:
                raise NotFoundError("Cliente não encontrado.")

        status = TransactionStatus.PAID if paid_at is not None else TransactionStatus.PENDING

        # Uma receita paga vinculada a um cliente É um atendimento: atualiza a
        # última visita sozinha, sem depender de o dono lembrar de marcar.
        if (
            client is not None
            and paid_at is not None
            and type == FinancialCategoryType.INCOME
            and is_newer_visit(client.last_visit_at, paid_at)
        ):
            await self._client_repository.update(client.id, last_visit_at=as_utc(paid_at))

        return await self._transaction_repository.create(
            category_id=category_id,
            type=type,
            amount_cents=amount_cents,
            description=description.strip(),
            status=status,
            due_date=due_date,
            paid_at=paid_at,
            notes=notes.strip() if notes else None,
            client_id=client_id,
            created_by=created_by,
        )
