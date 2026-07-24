from datetime import UTC, datetime

from beanie import PydanticObjectId

from app.core.tenant import get_current_company_id
from app.domain.client.entities import Client
from app.infrastructure.database.models.client import ClientDocument


def _to_entity(document: ClientDocument) -> Client:
    return Client(
        id=str(document.id),
        company_id=document.company_id,
        name=document.name,
        email=document.email,
        phone=document.phone,
        notes=document.notes,
        custom_fields=dict(document.custom_fields),
        is_active=document.is_active,
        created_at=document.created_at,
        updated_at=document.updated_at,
        return_interval_days=document.return_interval_days,
        last_visit_at=document.last_visit_at,
    )


class BeanieClientRepository:
    """Toda operação é automaticamente restrita à empresa do contexto de tenant atual."""

    async def create(
        self,
        *,
        name: str,
        email: str | None,
        phone: str | None,
        notes: str | None,
        custom_fields: dict[str, str],
        return_interval_days: int | None = None,
    ) -> Client:
        now = datetime.now(UTC)
        document = ClientDocument(
            company_id=get_current_company_id(),
            name=name,
            email=email,
            phone=phone,
            notes=notes,
            custom_fields=custom_fields,
            created_at=now,
            updated_at=now,
            return_interval_days=return_interval_days,
        )
        await document.insert()
        return _to_entity(document)

    async def get_by_id(self, client_id: str) -> Client | None:
        if not PydanticObjectId.is_valid(client_id):
            return None
        document = await ClientDocument.find_one(
            ClientDocument.id == PydanticObjectId(client_id),
            ClientDocument.company_id == get_current_company_id(),
        )
        return _to_entity(document) if document else None

    async def list_all(self, *, only_active: bool = True) -> list[Client]:
        query: dict[str, object] = {"company_id": get_current_company_id()}
        if only_active:
            query["is_active"] = True
        documents = await ClientDocument.find(query).to_list()
        return [_to_entity(document) for document in documents]

    async def update(self, client_id: str, **fields: object) -> Client | None:
        if not PydanticObjectId.is_valid(client_id):
            return None
        document = await ClientDocument.find_one(
            ClientDocument.id == PydanticObjectId(client_id),
            ClientDocument.company_id == get_current_company_id(),
        )
        if document is None:
            return None
        for field_name, value in fields.items():
            setattr(document, field_name, value)
        document.updated_at = datetime.now(UTC)
        await document.save()
        return _to_entity(document)
