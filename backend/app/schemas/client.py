from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class CreateClientRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    notes: str | None = Field(default=None, max_length=2000)
    custom_fields: dict[str, str] = Field(default_factory=dict)


class UpdateClientRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    notes: str | None = Field(default=None, max_length=2000)
    custom_fields: dict[str, str] | None = None
    is_active: bool | None = None


class ClientResponse(BaseModel):
    id: str
    company_id: str
    name: str
    email: str | None
    phone: str | None
    notes: str | None
    custom_fields: dict[str, str]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ClientSummaryResponse(BaseModel):
    client_id: str
    total_spent_cents: int
    purchase_count: int
    last_purchase_at: datetime | None
