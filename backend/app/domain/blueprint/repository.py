from typing import Protocol

from app.domain.blueprint.entities import (
    CompanyBlueprint,
    CustomFieldDefinition,
    KPIDefinition,
    SuggestedFinancialCategory,
)


class CompanyBlueprintRepository(Protocol):
    async def upsert(
        self,
        *,
        company_id: str,
        modules: list[str],
        financial_categories: list[SuggestedFinancialCategory],
        kpis: list[KPIDefinition],
        client_custom_fields: list[CustomFieldDefinition],
        ai_provider: str,
    ) -> CompanyBlueprint: ...

    async def get_by_company_id(self, company_id: str) -> CompanyBlueprint | None: ...
