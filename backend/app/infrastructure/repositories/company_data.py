from typing import Any

from beanie import PydanticObjectId

from app.infrastructure.database.models.appointment import AppointmentDocument
from app.infrastructure.database.models.catalog_item import CatalogItemDocument
from app.infrastructure.database.models.client import ClientDocument
from app.infrastructure.database.models.company import CompanyDocument
from app.infrastructure.database.models.company_blueprint import CompanyBlueprintDocument
from app.infrastructure.database.models.company_membership import CompanyMembershipDocument
from app.infrastructure.database.models.connection import ConnectionDocument
from app.infrastructure.database.models.employee import EmployeeDocument
from app.infrastructure.database.models.financial_category import FinancialCategoryDocument
from app.infrastructure.database.models.financial_transaction import FinancialTransactionDocument
from app.infrastructure.database.models.invitation import InvitationDocument
from app.infrastructure.database.models.stock_movement import StockMovementDocument

# Coleções ligadas à empresa por company_id (para export e purge).
_SCOPED_MODELS = [
    FinancialCategoryDocument,
    FinancialTransactionDocument,
    ClientDocument,
    CatalogItemDocument,
    StockMovementDocument,
    EmployeeDocument,
    AppointmentDocument,
    ConnectionDocument,
    CompanyBlueprintDocument,
]


def _serialize(document: Any) -> dict[str, Any]:
    data: dict[str, Any] = document.model_dump(mode="json")
    data["id"] = str(document.id)
    # Nunca exporta segredos de integração.
    data.pop("encrypted_secrets", None)
    return data


class BeanieCompanyDataService:
    """Adaptador único para export e purge dos dados de uma empresa."""

    async def export(self, company_id: str) -> dict[str, object]:
        result: dict[str, object] = {}
        if PydanticObjectId.is_valid(company_id):
            company = await CompanyDocument.get(PydanticObjectId(company_id))
            result["company"] = _serialize(company) if company else None
        for model in _SCOPED_MODELS:
            documents = await model.find({"company_id": company_id}).to_list()
            result[model.Settings.name] = [_serialize(doc) for doc in documents]
        return result

    async def erase(self, company_id: str) -> None:
        for model in _SCOPED_MODELS:
            await model.find({"company_id": company_id}).delete()
        await CompanyMembershipDocument.find(
            CompanyMembershipDocument.company_id == company_id
        ).delete()
        await InvitationDocument.find(InvitationDocument.company_id == company_id).delete()
        if PydanticObjectId.is_valid(company_id):
            company = await CompanyDocument.get(PydanticObjectId(company_id))
            if company is not None:
                await company.delete()
