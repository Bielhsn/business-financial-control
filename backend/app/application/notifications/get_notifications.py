from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum

from app.domain.financial.entities import FinancialCategoryType, TransactionStatus
from app.domain.financial.repository import FinancialTransactionRepository


class NotificationKind(StrEnum):
    OVERDUE = "overdue"
    DUE_SOON = "due_soon"


@dataclass
class Notification:
    kind: NotificationKind
    transaction_id: str
    description: str
    amount_cents: int
    type: FinancialCategoryType
    due_date: datetime


class GetNotificationsUseCase:
    """Notificações derivadas em tempo real dos lançamentos pendentes.

    Nada é persistido: uma conta paga some da lista sozinha — sem estado
    lido/não-lido para sincronizar nem notificações órfãs.
    """

    def __init__(self, transaction_repository: FinancialTransactionRepository) -> None:
        self._transaction_repository = transaction_repository

    async def execute(self, *, due_soon_days: int = 7) -> list[Notification]:
        pending = await self._transaction_repository.list_all(status=TransactionStatus.PENDING)
        now = datetime.now(UTC)
        horizon = now + timedelta(days=due_soon_days)
        notifications: list[Notification] = []

        for transaction in pending:
            if transaction.due_date is None:
                continue
            due = transaction.due_date
            if due.tzinfo is None:
                due = due.replace(tzinfo=UTC)
            if due < now:
                kind = NotificationKind.OVERDUE
            elif due <= horizon:
                kind = NotificationKind.DUE_SOON
            else:
                continue
            notifications.append(
                Notification(
                    kind=kind,
                    transaction_id=transaction.id,
                    description=transaction.description,
                    amount_cents=transaction.amount_cents,
                    type=transaction.type,
                    due_date=due,
                )
            )

        # Vencidas primeiro, depois por proximidade do vencimento.
        notifications.sort(key=lambda n: (n.kind != NotificationKind.OVERDUE, n.due_date))
        return notifications
