from datetime import UTC, datetime

from beanie import PydanticObjectId

from app.core.tenant import get_current_company_id
from app.domain.financial.entities import FinancialCategoryType
from app.domain.recurring.entities import RecurrenceFrequency, RecurringTransaction
from app.infrastructure.database.models.recurring_transaction import (
    RecurringTransactionDocument,
)


def _to_entity(document: RecurringTransactionDocument) -> RecurringTransaction:
    return RecurringTransaction(
        id=str(document.id),
        company_id=document.company_id,
        category_id=document.category_id,
        type=FinancialCategoryType(document.type),
        amount_cents=document.amount_cents,
        description=document.description,
        frequency=RecurrenceFrequency(document.frequency),
        anchor_day=document.anchor_day,
        next_run_date=document.next_run_date,
        active=document.active,
        notes=document.notes,
        client_id=document.client_id,
        created_by=document.created_by,
        created_at=document.created_at,
        updated_at=document.updated_at,
        last_run_at=document.last_run_at,
    )


class BeanieRecurringTransactionRepository:
    """Escopado por empresa (tenant) via contexto atual."""

    async def list_all(self) -> list[RecurringTransaction]:
        company_id = get_current_company_id()
        documents = await RecurringTransactionDocument.find(
            RecurringTransactionDocument.company_id == company_id
        ).to_list()
        return [_to_entity(document) for document in documents]

    async def _get_scoped(self, recurring_id: str) -> RecurringTransactionDocument | None:
        if not PydanticObjectId.is_valid(recurring_id):
            return None
        document = await RecurringTransactionDocument.get(PydanticObjectId(recurring_id))
        if document is None or document.company_id != get_current_company_id():
            return None
        return document

    async def get_by_id(self, recurring_id: str) -> RecurringTransaction | None:
        document = await self._get_scoped(recurring_id)
        return _to_entity(document) if document else None

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
    ) -> RecurringTransaction:
        now = datetime.now(UTC)
        document = RecurringTransactionDocument(
            company_id=get_current_company_id(),
            category_id=category_id,
            type=type.value,
            amount_cents=amount_cents,
            description=description,
            frequency=frequency.value,
            anchor_day=anchor_day,
            next_run_date=next_run_date,
            active=True,
            notes=notes,
            client_id=client_id,
            created_by=created_by,
            created_at=now,
            updated_at=now,
        )
        await document.insert()
        return _to_entity(document)

    async def update(self, recurring_id: str, **fields: object) -> RecurringTransaction | None:
        document = await self._get_scoped(recurring_id)
        if document is None:
            return None
        for name, value in fields.items():
            if isinstance(value, FinancialCategoryType | RecurrenceFrequency):
                value = value.value
            setattr(document, name, value)
        document.updated_at = datetime.now(UTC)
        await document.save()
        return _to_entity(document)

    async def delete(self, recurring_id: str) -> bool:
        document = await self._get_scoped(recurring_id)
        if document is None:
            return False
        await document.delete()
        return True

    async def list_due(self, as_of: datetime) -> list[RecurringTransaction]:
        company_id = get_current_company_id()
        documents = await RecurringTransactionDocument.find(
            RecurringTransactionDocument.company_id == company_id,
            RecurringTransactionDocument.active == True,  # noqa: E712
            RecurringTransactionDocument.next_run_date <= as_of,
        ).to_list()
        return [_to_entity(document) for document in documents]
