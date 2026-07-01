from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from app.domain.financial.entities import FinancialCategoryType


class CustomFieldType(StrEnum):
    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    BOOLEAN = "boolean"
    SELECT = "select"


@dataclass
class SuggestedFinancialCategory:
    """Sugestão da IA — vira uma `FinancialCategory` real ao ser importada (Etapa 5)."""

    name: str
    type: FinancialCategoryType


@dataclass
class KPIDefinition:
    key: str
    name: str
    description: str


@dataclass
class CustomFieldDefinition:
    key: str
    label: str
    type: CustomFieldType


@dataclass
class CompanyBlueprint:
    id: str
    company_id: str
    modules: list[str]
    financial_categories: list[SuggestedFinancialCategory]
    kpis: list[KPIDefinition]
    client_custom_fields: list[CustomFieldDefinition]
    ai_provider: str
    generated_at: datetime
