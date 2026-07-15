from datetime import UTC, datetime

from app.domain.blueprint.entities import (
    CompanyBlueprint,
    CustomFieldDefinition,
    CustomFieldType,
    KPIDefinition,
    SuggestedFinancialCategory,
)
from app.domain.dashboard.kpi_registry import KPIMetric
from app.domain.financial.entities import FinancialCategoryType
from app.infrastructure.database.models.company_blueprint import (
    CompanyBlueprintDocument,
    CustomFieldEmbedded,
    FinancialCategoryEmbedded,
    KPIEmbedded,
)


def _to_entity(document: CompanyBlueprintDocument) -> CompanyBlueprint:
    return CompanyBlueprint(
        id=str(document.id),
        company_id=document.company_id,
        modules=list(document.modules),
        financial_categories=[
            SuggestedFinancialCategory(name=item.name, type=FinancialCategoryType(item.type))
            for item in document.financial_categories
        ],
        kpis=[
            KPIDefinition(
                key=item.key,
                name=item.name,
                description=item.description,
                metric=KPIMetric(item.metric),
            )
            for item in document.kpis
        ],
        client_custom_fields=[
            CustomFieldDefinition(key=item.key, label=item.label, type=CustomFieldType(item.type))
            for item in document.client_custom_fields
        ],
        ai_provider=document.ai_provider,
        generated_at=document.generated_at,
        integrations=list(document.integrations),
    )


class BeanieCompanyBlueprintRepository:
    async def upsert(
        self,
        *,
        company_id: str,
        modules: list[str],
        financial_categories: list[SuggestedFinancialCategory],
        kpis: list[KPIDefinition],
        client_custom_fields: list[CustomFieldDefinition],
        ai_provider: str,
        integrations: list[str] | None = None,
    ) -> CompanyBlueprint:
        now = datetime.now(UTC)
        financial_categories_embedded = [
            FinancialCategoryEmbedded(name=item.name, type=item.type.value)
            for item in financial_categories
        ]
        kpis_embedded = [
            KPIEmbedded(
                key=item.key,
                name=item.name,
                description=item.description,
                metric=item.metric.value,
            )
            for item in kpis
        ]
        custom_fields_embedded = [
            CustomFieldEmbedded(key=item.key, label=item.label, type=item.type.value)
            for item in client_custom_fields
        ]

        existing = await CompanyBlueprintDocument.find_one(
            CompanyBlueprintDocument.company_id == company_id
        )
        if existing is not None:
            existing.modules = modules
            existing.financial_categories = financial_categories_embedded
            existing.kpis = kpis_embedded
            existing.client_custom_fields = custom_fields_embedded
            existing.ai_provider = ai_provider
            existing.integrations = integrations or []
            existing.generated_at = now
            await existing.save()
            return _to_entity(existing)

        document = CompanyBlueprintDocument(
            company_id=company_id,
            modules=modules,
            financial_categories=financial_categories_embedded,
            kpis=kpis_embedded,
            client_custom_fields=custom_fields_embedded,
            ai_provider=ai_provider,
            integrations=integrations or [],
            generated_at=now,
        )
        await document.insert()
        return _to_entity(document)

    async def get_by_company_id(self, company_id: str) -> CompanyBlueprint | None:
        document = await CompanyBlueprintDocument.find_one(
            CompanyBlueprintDocument.company_id == company_id
        )
        return _to_entity(document) if document else None
