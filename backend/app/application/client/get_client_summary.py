from app.core.exceptions import NotFoundError
from app.domain.client.entities import ClientSummary
from app.domain.client.repository import ClientRepository
from app.domain.financial.repository import FinancialTransactionRepository


class GetClientSummaryUseCase:
    def __init__(
        self,
        client_repository: ClientRepository,
        transaction_repository: FinancialTransactionRepository,
    ) -> None:
        self._client_repository = client_repository
        self._transaction_repository = transaction_repository

    async def execute(self, *, client_id: str) -> ClientSummary:
        client = await self._client_repository.get_by_id(client_id)
        if client is None:
            raise NotFoundError("Cliente não encontrado.")

        purchases = await self._transaction_repository.list_paid_for_client(client_id)
        paid_dates = [p.paid_at for p in purchases if p.paid_at is not None]

        return ClientSummary(
            client_id=client_id,
            total_spent_cents=sum(p.amount_cents for p in purchases),
            purchase_count=len(purchases),
            last_purchase_at=max(paid_dates) if paid_dates else None,
        )
