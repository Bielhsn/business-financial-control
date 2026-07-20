from datetime import UTC, datetime

from beanie import PydanticObjectId

from app.core.tenant import get_current_company_id
from app.domain.financial.entities import (
    FinancialCategoryType,
    FinancialTransaction,
    TransactionStatus,
)
from app.infrastructure.database.models.financial_transaction import FinancialTransactionDocument


def _to_entity(document: FinancialTransactionDocument) -> FinancialTransaction:
    return FinancialTransaction(
        id=str(document.id),
        company_id=document.company_id,
        category_id=document.category_id,
        type=FinancialCategoryType(document.type),
        amount_cents=document.amount_cents,
        description=document.description,
        status=TransactionStatus(document.status),
        due_date=document.due_date,
        paid_at=document.paid_at,
        notes=document.notes,
        client_id=document.client_id,
        created_by=document.created_by,
        created_at=document.created_at,
        updated_at=document.updated_at,
        external_ref=document.external_ref,
    )


class BeanieFinancialTransactionRepository:
    """Toda operação é automaticamente restrita à empresa do contexto de tenant atual."""

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
        client_id: str | None,
        created_by: str,
        external_ref: str | None = None,
    ) -> FinancialTransaction:
        now = datetime.now(UTC)
        document = FinancialTransactionDocument(
            company_id=get_current_company_id(),
            category_id=category_id,
            type=type.value,
            amount_cents=amount_cents,
            description=description,
            status=status.value,
            due_date=due_date,
            paid_at=paid_at,
            notes=notes,
            client_id=client_id,
            created_by=created_by,
            external_ref=external_ref,
            created_at=now,
            updated_at=now,
        )
        await document.insert()
        return _to_entity(document)

    async def find_by_external_ref(self, external_ref: str) -> FinancialTransaction | None:
        document = await FinancialTransactionDocument.find_one(
            FinancialTransactionDocument.company_id == get_current_company_id(),
            FinancialTransactionDocument.external_ref == external_ref,
        )
        return _to_entity(document) if document else None

    async def get_by_id(self, transaction_id: str) -> FinancialTransaction | None:
        if not PydanticObjectId.is_valid(transaction_id):
            return None
        document = await FinancialTransactionDocument.find_one(
            FinancialTransactionDocument.id == PydanticObjectId(transaction_id),
            FinancialTransactionDocument.company_id == get_current_company_id(),
        )
        return _to_entity(document) if document else None

    async def list_all(
        self,
        *,
        type: FinancialCategoryType | None = None,
        status: TransactionStatus | None = None,
    ) -> list[FinancialTransaction]:
        query: dict[str, object] = {"company_id": get_current_company_id()}
        if type is not None:
            query["type"] = type.value
        if status is not None:
            query["status"] = status.value
        documents = await FinancialTransactionDocument.find(query).to_list()
        return [_to_entity(document) for document in documents]

    async def list_paid_for_client(self, client_id: str) -> list[FinancialTransaction]:
        documents = await FinancialTransactionDocument.find(
            {
                "company_id": get_current_company_id(),
                "client_id": client_id,
                "status": TransactionStatus.PAID.value,
            }
        ).to_list()
        return [_to_entity(document) for document in documents]

    async def update(self, transaction_id: str, **fields: object) -> FinancialTransaction | None:
        if not PydanticObjectId.is_valid(transaction_id):
            return None
        document = await FinancialTransactionDocument.find_one(
            FinancialTransactionDocument.id == PydanticObjectId(transaction_id),
            FinancialTransactionDocument.company_id == get_current_company_id(),
        )
        if document is None:
            return None
        for field_name, value in fields.items():
            setattr(document, field_name, value)
        document.updated_at = datetime.now(UTC)
        await document.save()
        return _to_entity(document)

    async def sum_paid_between(
        self, *, type: FinancialCategoryType, start: datetime, end: datetime
    ) -> int:
        documents = await FinancialTransactionDocument.find(
            {
                "company_id": get_current_company_id(),
                "type": type.value,
                "status": TransactionStatus.PAID.value,
                "paid_at": {"$gte": start, "$lte": end},
            }
        ).to_list()
        return sum(document.amount_cents for document in documents)

    async def list_paid_between(
        self, *, start: datetime, end: datetime
    ) -> list[FinancialTransaction]:
        documents = await FinancialTransactionDocument.find(
            {
                "company_id": get_current_company_id(),
                "status": TransactionStatus.PAID.value,
                "paid_at": {"$gte": start, "$lte": end},
            }
        ).to_list()
        return [_to_entity(document) for document in documents]
