from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class FinancialCategoryType(StrEnum):
    INCOME = "income"
    EXPENSE = "expense"


class CustomFieldType(StrEnum):
    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    BOOLEAN = "boolean"
    SELECT = "select"


@dataclass
class FinancialCategory:
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
    financial_categories: list[FinancialCategory]
    kpis: list[KPIDefinition]
    client_custom_fields: list[CustomFieldDefinition]
    ai_provider: str
    generated_at: datetime
