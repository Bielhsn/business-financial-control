from datetime import UTC, datetime

from beanie import PydanticObjectId
from pymongo.errors import DuplicateKeyError

from app.core.exceptions import ConflictError
from app.core.tenant import get_current_company_id
from app.domain.financial.entities import FinancialCategory, FinancialCategoryType
from app.infrastructure.database.models.financial_category import FinancialCategoryDocument


def _to_entity(document: FinancialCategoryDocument) -> FinancialCategory:
    return FinancialCategory(
        id=str(document.id),
        company_id=document.company_id,
        name=document.name,
        type=FinancialCategoryType(document.type),
        is_active=document.is_active,
        created_at=document.created_at,
    )


class BeanieFinancialCategoryRepository:
    """Toda operação é automaticamente restrita à empresa do contexto de tenant atual."""

    async def create(self, *, name: str, type: FinancialCategoryType) -> FinancialCategory:
        document = FinancialCategoryDocument(
            company_id=get_current_company_id(),
            name=name,
            type=type.value,
            created_at=datetime.now(UTC),
        )
        try:
            await document.insert()
        except DuplicateKeyError as exc:
            raise ConflictError("Já existe uma categoria com este nome e tipo.") from exc
        return _to_entity(document)

    async def get_by_id(self, category_id: str) -> FinancialCategory | None:
        if not PydanticObjectId.is_valid(category_id):
            return None
        document = await FinancialCategoryDocument.find_one(
            FinancialCategoryDocument.id == PydanticObjectId(category_id),
            FinancialCategoryDocument.company_id == get_current_company_id(),
        )
        return _to_entity(document) if document else None

    async def get_by_name_and_type(
        self, name: str, type: FinancialCategoryType
    ) -> FinancialCategory | None:
        document = await FinancialCategoryDocument.find_one(
            FinancialCategoryDocument.company_id == get_current_company_id(),
            FinancialCategoryDocument.name == name,
            FinancialCategoryDocument.type == type.value,
        )
        return _to_entity(document) if document else None

    async def list_all(self, *, only_active: bool = True) -> list[FinancialCategory]:
        query: dict[str, object] = {"company_id": get_current_company_id()}
        if only_active:
            query["is_active"] = True
        documents = await FinancialCategoryDocument.find(query).to_list()
        return [_to_entity(document) for document in documents]

    async def update(self, category_id: str, **fields: object) -> FinancialCategory | None:
        if not PydanticObjectId.is_valid(category_id):
            return None
        document = await FinancialCategoryDocument.find_one(
            FinancialCategoryDocument.id == PydanticObjectId(category_id),
            FinancialCategoryDocument.company_id == get_current_company_id(),
        )
        if document is None:
            return None
        for field_name, value in fields.items():
            setattr(document, field_name, value)
        await document.save()
        return _to_entity(document)
