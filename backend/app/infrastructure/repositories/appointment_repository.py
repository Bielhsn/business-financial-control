from datetime import UTC, datetime

from beanie import PydanticObjectId

from app.core.tenant import get_current_company_id
from app.domain.appointment.entities import Appointment, AppointmentStatus
from app.infrastructure.database.models.appointment import AppointmentDocument


def _to_entity(document: AppointmentDocument) -> Appointment:
    return Appointment(
        id=str(document.id),
        company_id=document.company_id,
        title=document.title,
        starts_at=document.starts_at,
        duration_minutes=document.duration_minutes,
        status=AppointmentStatus(document.status),
        client_id=document.client_id,
        client_name=document.client_name,
        employee_id=document.employee_id,
        employee_name=document.employee_name,
        catalog_item_id=document.catalog_item_id,
        price_cents=document.price_cents,
        notes=document.notes,
        revenue_transaction_id=document.revenue_transaction_id,
        created_by=document.created_by,
        created_at=document.created_at,
        updated_at=document.updated_at,
    )


class BeanieAppointmentRepository:
    """Toda operação é automaticamente restrita à empresa do contexto de tenant atual."""

    async def create(
        self,
        *,
        title: str,
        starts_at: datetime,
        duration_minutes: int,
        client_id: str | None,
        client_name: str | None,
        employee_id: str | None,
        employee_name: str | None,
        catalog_item_id: str | None,
        price_cents: int | None,
        notes: str | None,
        created_by: str,
    ) -> Appointment:
        now = datetime.now(UTC)
        document = AppointmentDocument(
            company_id=get_current_company_id(),
            title=title,
            starts_at=starts_at,
            duration_minutes=duration_minutes,
            status=AppointmentStatus.SCHEDULED.value,
            client_id=client_id,
            client_name=client_name,
            employee_id=employee_id,
            employee_name=employee_name,
            catalog_item_id=catalog_item_id,
            price_cents=price_cents,
            notes=notes,
            created_by=created_by,
            created_at=now,
            updated_at=now,
        )
        await document.insert()
        return _to_entity(document)

    async def get_by_id(self, appointment_id: str) -> Appointment | None:
        document = await self._get_document(appointment_id)
        return _to_entity(document) if document else None

    async def list_between(
        self,
        *,
        start: datetime,
        end: datetime,
        employee_id: str | None = None,
    ) -> list[Appointment]:
        query: dict[str, object] = {
            "company_id": get_current_company_id(),
            "starts_at": {"$gte": start, "$lt": end},
        }
        if employee_id is not None:
            query["employee_id"] = employee_id
        documents = await AppointmentDocument.find(query).sort("+starts_at").to_list()
        return [_to_entity(document) for document in documents]

    async def update(self, appointment_id: str, **fields: object) -> Appointment | None:
        document = await self._get_document(appointment_id)
        if document is None:
            return None
        for field_name, value in fields.items():
            setattr(document, field_name, value)
        document.updated_at = datetime.now(UTC)
        await document.save()
        return _to_entity(document)

    async def _get_document(self, appointment_id: str) -> AppointmentDocument | None:
        if not PydanticObjectId.is_valid(appointment_id):
            return None
        return await AppointmentDocument.find_one(
            AppointmentDocument.id == PydanticObjectId(appointment_id),
            AppointmentDocument.company_id == get_current_company_id(),
        )
