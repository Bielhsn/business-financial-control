from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.blueprint.entities import CustomFieldType
from app.domain.dashboard.kpi_registry import KPIMetric
from app.domain.financial.entities import FinancialCategoryType


class GenerateBlueprintRequest(BaseModel):
    additional_context: str | None = Field(default=None, max_length=2000)


class FinancialCategoryResponse(BaseModel):
    name: str
    type: FinancialCategoryType


class KPIResponse(BaseModel):
    key: str
    name: str
    description: str
    metric: KPIMetric


class CustomFieldResponse(BaseModel):
    key: str
    label: str
    type: CustomFieldType


class CompanyBlueprintResponse(BaseModel):
    id: str
    company_id: str
    modules: list[str]
    financial_categories: list[FinancialCategoryResponse]
    kpis: list[KPIResponse]
    client_custom_fields: list[CustomFieldResponse]
    integrations: list[str]
    ai_provider: str
    generated_at: datetime
