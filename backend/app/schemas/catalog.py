from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.catalog.entities import CatalogItemKind


class CreateCatalogItemRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    price_cents: int = Field(gt=0)
    kind: CatalogItemKind
    tracks_inventory: bool = False
    stock_quantity: int | None = Field(default=None, ge=0)


class UpdateCatalogItemRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    price_cents: int | None = Field(default=None, gt=0)
    is_active: bool | None = None


class AdjustStockRequest(BaseModel):
    delta: int
    reason: str = Field(min_length=1, max_length=500)


class CatalogItemResponse(BaseModel):
    id: str
    company_id: str
    name: str
    description: str | None
    price_cents: int
    kind: CatalogItemKind
    tracks_inventory: bool
    stock_quantity: int | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
