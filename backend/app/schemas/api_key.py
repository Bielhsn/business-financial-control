from datetime import datetime

from pydantic import BaseModel, Field


class CreateApiKeyRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class ApiKeyResponse(BaseModel):
    id: str
    name: str
    prefix: str
    created_at: datetime
    last_used_at: datetime | None
    revoked: bool


class CreatedApiKeyResponse(ApiKeyResponse):
    # A chave crua só aparece nesta resposta de criação — nunca mais.
    raw_key: str


class PublicSummaryResponse(BaseModel):
    company_id: str
    month_income_cents: int
    month_expense_cents: int
    month_net_cents: int
    health_score: int
    health_rating: str
