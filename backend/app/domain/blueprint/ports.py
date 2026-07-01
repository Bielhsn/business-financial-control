from dataclasses import dataclass
from typing import Protocol

from app.domain.blueprint.entities import (
    CustomFieldDefinition,
    KPIDefinition,
    SuggestedFinancialCategory,
)
from app.domain.company.entities import Company


@dataclass
class CompanyBlueprintDraft:
    modules: list[str]
    financial_categories: list[SuggestedFinancialCategory]
    kpis: list[KPIDefinition]
    client_custom_fields: list[CustomFieldDefinition]


class AIProviderPort(Protocol):
    async def generate_company_blueprint(
        self, *, company: Company, additional_context: str | None
    ) -> CompanyBlueprintDraft: ...
