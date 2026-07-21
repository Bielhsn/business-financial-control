from datetime import datetime
from typing import Protocol

from app.domain.financial.entities import FinancialCategoryType
from app.domain.recurring.entities import RecurrenceFrequency, RecurringTransaction


class RecurringTransactionRepository(Protocol):
    """Recorrências escopadas por empresa (tenant) via contexto atual. O chamador
    nunca informa `company_id`."""

    async def list_all(self) -> list[RecurringTransaction]: ...

    async def get_by_id(self, recurring_id: str) -> RecurringTransaction | None: ...

    async def create(
        self,
        *,
        category_id: str,
        type: FinancialCategoryType,
        amount_cents: int,
        description: str,
        frequency: RecurrenceFrequency,
        anchor_day: int,
        next_run_date: datetime,
        notes: str | None,
        client_id: str | None,
        created_by: str,
    ) -> RecurringTransaction: ...

    async def update(self, recurring_id: str, **fields: object) -> RecurringTransaction | None: ...

    async def delete(self, recurring_id: str) -> bool: ...

    async def list_due(self, as_of: datetime) -> list[RecurringTransaction]:
        """Recorrências ativas cuja próxima data já venceu (<= as_of)."""
        ...
