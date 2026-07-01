from datetime import UTC, datetime

from beanie import PydanticObjectId

from app.domain.company.entities import Company
from app.infrastructure.database.models.company import CompanyDocument


def _to_entity(document: CompanyDocument) -> Company:
    return Company(
        id=str(document.id),
        name=document.name,
        segment=document.segment,
        employee_count=document.employee_count,
        average_customer_count=document.average_customer_count,
        city=document.city,
        state=document.state,
        country=document.country,
        size=document.size,
        tax_regime=document.tax_regime,
        additional_info=document.additional_info,
        is_active=document.is_active,
        created_at=document.created_at,
        updated_at=document.updated_at,
    )


class BeanieCompanyRepository:
    async def create(
        self,
        *,
        name: str,
        segment: str,
        employee_count: int,
        average_customer_count: int,
        city: str,
        state: str,
        country: str,
        size: str,
        tax_regime: str | None,
        additional_info: str | None,
    ) -> Company:
        now = datetime.now(UTC)
        document = CompanyDocument(
            name=name,
            segment=segment,
            employee_count=employee_count,
            average_customer_count=average_customer_count,
            city=city,
            state=state,
            country=country,
            size=size,
            tax_regime=tax_regime,
            additional_info=additional_info,
            created_at=now,
            updated_at=now,
        )
        await document.insert()
        return _to_entity(document)

    async def get_by_id(self, company_id: str) -> Company | None:
        if not PydanticObjectId.is_valid(company_id):
            return None
        document = await CompanyDocument.get(PydanticObjectId(company_id))
        return _to_entity(document) if document else None

    async def update(self, company_id: str, **fields: object) -> Company | None:
        if not PydanticObjectId.is_valid(company_id):
            return None
        document = await CompanyDocument.get(PydanticObjectId(company_id))
        if document is None:
            return None
        for field_name, value in fields.items():
            setattr(document, field_name, value)
        document.updated_at = datetime.now(UTC)
        await document.save()
        return _to_entity(document)

    async def delete(self, company_id: str) -> None:
        if not PydanticObjectId.is_valid(company_id):
            return
        document = await CompanyDocument.get(PydanticObjectId(company_id))
        if document is not None:
            await document.delete()
