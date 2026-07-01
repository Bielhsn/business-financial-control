from datetime import datetime

from beanie import Document, Indexed
from pydantic import BaseModel


class FinancialCategoryEmbedded(BaseModel):
    name: str
    type: str


class KPIEmbedded(BaseModel):
    key: str
    name: str
    description: str


class CustomFieldEmbedded(BaseModel):
    key: str
    label: str
    type: str


class CompanyBlueprintDocument(Document):
    company_id: Indexed(str, unique=True)  # type: ignore[valid-type]
    modules: list[str]
    financial_categories: list[FinancialCategoryEmbedded]
    kpis: list[KPIEmbedded]
    client_custom_fields: list[CustomFieldEmbedded]
    ai_provider: str
    generated_at: datetime

    class Settings:
        name = "company_blueprints"
