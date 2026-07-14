from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.company.roles import CompanyRole


class CreateCompanyRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    segment: str = Field(min_length=1, max_length=200)
    employee_count: int = Field(ge=0)
    average_customer_count: int = Field(ge=0)
    city: str = Field(min_length=1, max_length=200)
    state: str = Field(min_length=1, max_length=200)
    country: str = Field(min_length=1, max_length=200)
    size: str = Field(min_length=1, max_length=100)
    tax_regime: str | None = Field(default=None, max_length=200)
    additional_info: str | None = Field(default=None, max_length=2000)
    currency: str = Field(default="BRL", pattern=r"^[A-Za-z]{3}$")
    sales_channels: list[Annotated[str, Field(min_length=1, max_length=100)]] = Field(
        default_factory=list, max_length=15
    )
    sales_mode: str | None = Field(default=None, max_length=200)
    main_offerings: str | None = Field(default=None, max_length=1000)


class UpdateCompanyRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    segment: str | None = Field(default=None, min_length=1, max_length=200)
    employee_count: int | None = Field(default=None, ge=0)
    average_customer_count: int | None = Field(default=None, ge=0)
    city: str | None = Field(default=None, min_length=1, max_length=200)
    state: str | None = Field(default=None, min_length=1, max_length=200)
    country: str | None = Field(default=None, min_length=1, max_length=200)
    size: str | None = Field(default=None, min_length=1, max_length=100)
    tax_regime: str | None = Field(default=None, max_length=200)
    additional_info: str | None = Field(default=None, max_length=2000)
    currency: str | None = Field(default=None, pattern=r"^[A-Za-z]{3}$")
    sales_channels: list[Annotated[str, Field(min_length=1, max_length=100)]] | None = Field(
        default=None, max_length=15
    )
    sales_mode: str | None = Field(default=None, max_length=200)
    main_offerings: str | None = Field(default=None, max_length=1000)
    # Branding (white-label light). Logo como data URL de imagem, limitada a ~150 KB
    # de arquivo (~200k chars em base64) — suficiente para logos, pequeno para o Mongo.
    brand_logo: str | None = Field(default=None, max_length=200_000)
    brand_primary_color: str | None = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")
    brand_theme: str | None = Field(default=None, pattern=r"^(light|dark)$")

    @field_validator("brand_logo")
    @classmethod
    def _logo_must_be_image_data_url(cls, value: str | None) -> str | None:
        if value is not None and not value.startswith("data:image/"):
            raise ValueError("O logo deve ser uma imagem (data URL image/*).")
        return value


class CompanyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    segment: str
    employee_count: int
    average_customer_count: int
    city: str
    state: str
    country: str
    size: str
    tax_regime: str | None
    additional_info: str | None
    currency: str
    sales_channels: list[str]
    sales_mode: str | None
    main_offerings: str | None
    brand_logo: str | None
    brand_primary_color: str | None
    brand_theme: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CompanyWithRoleResponse(BaseModel):
    company: CompanyResponse
    role: CompanyRole
