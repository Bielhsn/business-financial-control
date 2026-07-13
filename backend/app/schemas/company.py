from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

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
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CompanyWithRoleResponse(BaseModel):
    company: CompanyResponse
    role: CompanyRole
