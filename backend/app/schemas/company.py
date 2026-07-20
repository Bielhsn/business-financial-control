from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.domain.company.cnpj import is_valid_cnpj, normalize_cnpj
from app.domain.company.roles import CompanyRole


def _validate_optional_cnpj(value: str | None) -> str | None:
    if value is None or value.strip() == "":
        return None
    normalized = normalize_cnpj(value)
    if not is_valid_cnpj(normalized):
        raise ValueError("CNPJ inválido.")
    return normalized


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
    legal_name: str | None = Field(default=None, max_length=200)
    trade_name: str | None = Field(default=None, max_length=200)
    cnpj: str | None = Field(default=None, max_length=20)
    subsegment: str | None = Field(default=None, max_length=200)
    monthly_revenue_cents: int | None = Field(default=None, ge=0)
    phone: str | None = Field(default=None, max_length=40)
    email: str | None = Field(default=None, max_length=200)
    website: str | None = Field(default=None, max_length=300)
    social_links: dict[str, str] = Field(default_factory=dict)

    @field_validator("cnpj")
    @classmethod
    def _validate_cnpj(cls, value: str | None) -> str | None:
        return _validate_optional_cnpj(value)


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
    legal_name: str | None = Field(default=None, max_length=200)
    trade_name: str | None = Field(default=None, max_length=200)
    cnpj: str | None = Field(default=None, max_length=20)
    subsegment: str | None = Field(default=None, max_length=200)
    monthly_revenue_cents: int | None = Field(default=None, ge=0)
    phone: str | None = Field(default=None, max_length=40)
    email: str | None = Field(default=None, max_length=200)
    website: str | None = Field(default=None, max_length=300)
    social_links: dict[str, str] | None = None

    @field_validator("brand_logo")
    @classmethod
    def _logo_must_be_image_data_url(cls, value: str | None) -> str | None:
        if value is not None and not value.startswith("data:image/"):
            raise ValueError("O logo deve ser uma imagem (data URL image/*).")
        return value

    @field_validator("cnpj")
    @classmethod
    def _validate_cnpj(cls, value: str | None) -> str | None:
        return _validate_optional_cnpj(value)


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
    legal_name: str | None
    trade_name: str | None
    cnpj: str | None
    subsegment: str | None
    monthly_revenue_cents: int | None
    phone: str | None
    email: str | None
    website: str | None
    social_links: dict[str, str]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CompanyWithRoleResponse(BaseModel):
    company: CompanyResponse
    role: CompanyRole


class MemberResponse(BaseModel):
    user_id: str
    email: str
    full_name: str
    role: CompanyRole


class ChangeRoleRequest(BaseModel):
    role: CompanyRole


class InviteMemberRequest(BaseModel):
    email: EmailStr
    role: CompanyRole


class InvitationResponse(BaseModel):
    id: str
    email: str
    role: CompanyRole
    status: str
    created_at: datetime
    expires_at: datetime


class AcceptInvitationRequest(BaseModel):
    token: str = Field(min_length=1)
