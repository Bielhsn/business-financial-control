from datetime import UTC, datetime

from app.application.client.visit_tracking import record_visit_if_newer
from app.core.exceptions import ConflictError, NotFoundError
from app.domain.client.repository import ClientRepository
from app.domain.financial.entities import (
    FinancialCategoryType,
    FinancialTransaction,
    TransactionStatus,
)
from app.domain.financial.repository import FinancialTransactionRepository


class MarkTransactionPaidUseCase:
    def __init__(
        self,
        transaction_repository: FinancialTransactionRepository,
        client_repository: ClientRepository | None = None,
    ) -> None:
        self._transaction_repository = transaction_repository
        self._client_repository = client_repository

    async def execute(
        self, *, transaction_id: str, paid_at: datetime | None = None
    ) -> FinancialTransaction:
        transaction = await self._transaction_repository.get_by_id(transaction_id)
        if transaction is None:
            raise NotFoundError("Lançamento não encontrado.")
        if transaction.status == TransactionStatus.CANCELLED:
            raise ConflictError("Um lançamento cancelado não pode ser marcado como pago.")
        if transaction.status == TransactionStatus.PAID:
            return transaction

        moment = paid_at or datetime.now(UTC)
        updated = await self._transaction_repository.update(
            transaction_id,
            status=TransactionStatus.PAID,
            paid_at=moment,
        )
        assert updated is not None

        # Receber de um cliente também conta como atendimento (mesma regra da
        # criação já paga), para a cadência de retorno ficar correta.
        if (
            self._client_repository is not None
            and updated.client_id is not None
            and updated.type == FinancialCategoryType.INCOME
        ):
            await record_visit_if_newer(
                self._client_repository, client_id=updated.client_id, visited_at=moment
            )
        return updated
