from app.core.exceptions import ConflictError, NotFoundError
from app.domain.financial.entities import FinancialTransaction, TransactionStatus
from app.domain.financial.repository import FinancialTransactionRepository


class CancelTransactionUseCase:
    """Só é possível cancelar lançamentos pendentes. Um lançamento já pago exige
    um estorno/ajuste (fora do escopo desta etapa), não um simples cancelamento,
    para preservar a integridade histórica do fluxo de caixa."""

    def __init__(self, transaction_repository: FinancialTransactionRepository) -> None:
        self._transaction_repository = transaction_repository

    async def execute(self, *, transaction_id: str) -> FinancialTransaction:
        transaction = await self._transaction_repository.get_by_id(transaction_id)
        if transaction is None:
            raise NotFoundError("Lançamento não encontrado.")
        if transaction.status != TransactionStatus.PENDING:
            raise ConflictError("Apenas lançamentos pendentes podem ser cancelados.")

        updated = await self._transaction_repository.update(
            transaction_id, status=TransactionStatus.CANCELLED
        )
        assert updated is not None
        return updated
