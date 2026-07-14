from datetime import UTC, datetime

from beanie import PydanticObjectId

from app.core.tenant import get_current_company_id
from app.domain.employee.entities import Employee
from app.infrastructure.database.models.employee import EmployeeDocument


def _to_entity(document: EmployeeDocument) -> Employee:
    return Employee(
        id=str(document.id),
        company_id=document.company_id,
        name=document.name,
        email=document.email,
        phone=document.phone,
        role_title=document.role_title,
        is_active=document.is_active,
        created_at=document.created_at,
        updated_at=document.updated_at,
    )


class BeanieEmployeeRepository:
    """Toda operação é automaticamente restrita à empresa do contexto de tenant atual."""

    async def create(
        self, *, name: str, email: str | None, phone: str | None, role_title: str | None
    ) -> Employee:
        now = datetime.now(UTC)
        document = EmployeeDocument(
            company_id=get_current_company_id(),
            name=name,
            email=email,
            phone=phone,
            role_title=role_title,
            created_at=now,
            updated_at=now,
        )
        await document.insert()
        return _to_entity(document)

    async def get_by_id(self, employee_id: str) -> Employee | None:
        if not PydanticObjectId.is_valid(employee_id):
            return None
        document = await EmployeeDocument.find_one(
            EmployeeDocument.id == PydanticObjectId(employee_id),
            EmployeeDocument.company_id == get_current_company_id(),
        )
        return _to_entity(document) if document else None

    async def list_all(self, *, only_active: bool = True) -> list[Employee]:
        query: dict[str, object] = {"company_id": get_current_company_id()}
        if only_active:
            query["is_active"] = True
        documents = await EmployeeDocument.find(query).to_list()
        return [_to_entity(document) for document in documents]

    async def update(self, employee_id: str, **fields: object) -> Employee | None:
        if not PydanticObjectId.is_valid(employee_id):
            return None
        document = await EmployeeDocument.find_one(
            EmployeeDocument.id == PydanticObjectId(employee_id),
            EmployeeDocument.company_id == get_current_company_id(),
        )
        if document is None:
            return None
        for field_name, value in fields.items():
            setattr(document, field_name, value)
        document.updated_at = datetime.now(UTC)
        await document.save()
        return _to_entity(document)
