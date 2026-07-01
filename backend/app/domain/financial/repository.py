from datetime import datetime
from typing import Protocol

from app.domain.financial.entities import (
    FinancialCategory,
    FinancialCategoryType,
    FinancialTransaction,
    TransactionStatus,
)


class FinancialCategoryRepository(Protocol):
    """Toda implementação filtra/carimba pela empresa do contexto de tenant atual
    (`core.tenant.get_current_company_id()`) — o chamador nunca informa `company_id`."""

    async def create(self, *, name: str, type: FinancialCategoryType) -> FinancialCategory: ...

    async def get_by_id(self, category_id: str) -> FinancialCategory | None: ...

    async def get_by_name_and_type(
        self, name: str, type: FinancialCategoryType
    ) -> FinancialCategory | None: ...

    async def list_all(self, *, only_active: bool = True) -> list[FinancialCategory]: ...

    async def update(self, category_id: str, **fields: object) -> FinancialCategory | None: ...


class FinancialTransactionRepository(Protocol):
    """Toda implementação filtra/carimba pela empresa do contexto de tenant atual
    (`core.tenant.get_current_company_id()`) — o chamador nunca informa `company_id`."""

    async def create(
        self,
        *,
        category_id: str,
        type: FinancialCategoryType,
        amount_cents: int,
        description: str,
        status: TransactionStatus,
        due_date: datetime | None,
        paid_at: datetime | None,
        notes: str | None,
        created_by: str,
    ) -> FinancialTransaction: ...

    async def get_by_id(self, transaction_id: str) -> FinancialTransaction | None: ...

    async def list_all(
        self,
        *,
        type: FinancialCategoryType | None = None,
        status: TransactionStatus | None = None,
    ) -> list[FinancialTransaction]: ...

    async def update(
        self, transaction_id: str, **fields: object
    ) -> FinancialTransaction | None: ...

    async def sum_paid_between(
        self, *, type: FinancialCategoryType, start: datetime, end: datetime
    ) -> int: ...
