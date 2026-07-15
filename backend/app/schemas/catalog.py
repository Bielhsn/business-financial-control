from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.domain.catalog.entities import CatalogItemKind

# Cada imagem como data URL, limitada a ~150 KB de arquivo (~200k chars em
# base64) — mesmo padrão do logo da empresa. Máximo de 6 imagens por item.
_MAX_IMAGE_CHARS = 200_000
_MAX_IMAGES = 6


class ProductVariantPayload(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    sku: str | None = Field(default=None, max_length=64)
    barcode: str | None = Field(default=None, max_length=64)
    price_cents: int | None = Field(default=None, gt=0)
    promo_price_cents: int | None = Field(default=None, gt=0)
    stock_quantity: int = Field(default=0, ge=0)


def _validate_images(images: list[str]) -> list[str]:
    if len(images) > _MAX_IMAGES:
        raise ValueError(f"No máximo {_MAX_IMAGES} imagens por item.")
    for image in images:
        if not image.startswith("data:image/"):
            raise ValueError("Cada imagem deve ser uma data URL image/*.")
        if len(image) > _MAX_IMAGE_CHARS:
            raise ValueError("Cada imagem deve ter no máximo ~150 KB.")
    return images


class CreateCatalogItemRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    price_cents: int = Field(gt=0)
    kind: CatalogItemKind
    tracks_inventory: bool = False
    stock_quantity: int | None = Field(default=None, ge=0)
    sku: str | None = Field(default=None, max_length=64)
    barcode: str | None = Field(default=None, max_length=64)
    brand: str | None = Field(default=None, max_length=120)
    supplier: str | None = Field(default=None, max_length=200)
    category: str | None = Field(default=None, max_length=120)
    subcategory: str | None = Field(default=None, max_length=120)
    short_description: str | None = Field(default=None, max_length=300)
    tags: list[str] = Field(default_factory=list, max_length=20)
    cost_price_cents: int | None = Field(default=None, ge=0)
    promo_price_cents: int | None = Field(default=None, gt=0)
    min_stock: int | None = Field(default=None, ge=0)
    max_stock: int | None = Field(default=None, ge=0)
    stock_location: str | None = Field(default=None, max_length=200)
    images: list[str] = Field(default_factory=list)
    variants: list[ProductVariantPayload] = Field(default_factory=list, max_length=50)

    @field_validator("tags")
    @classmethod
    def _tags_max_length(cls, value: list[str]) -> list[str]:
        for tag in value:
            if len(tag) > 40:
                raise ValueError("Cada tag deve ter no máximo 40 caracteres.")
        return value

    @field_validator("images")
    @classmethod
    def _images_must_be_data_urls(cls, value: list[str]) -> list[str]:
        return _validate_images(value)


class UpdateCatalogItemRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    price_cents: int | None = Field(default=None, gt=0)
    is_active: bool | None = None
    sku: str | None = Field(default=None, max_length=64)
    barcode: str | None = Field(default=None, max_length=64)
    brand: str | None = Field(default=None, max_length=120)
    supplier: str | None = Field(default=None, max_length=200)
    category: str | None = Field(default=None, max_length=120)
    subcategory: str | None = Field(default=None, max_length=120)
    short_description: str | None = Field(default=None, max_length=300)
    tags: list[str] | None = Field(default=None, max_length=20)
    cost_price_cents: int | None = Field(default=None, ge=0)
    promo_price_cents: int | None = Field(default=None, gt=0)
    min_stock: int | None = Field(default=None, ge=0)
    max_stock: int | None = Field(default=None, ge=0)
    stock_location: str | None = Field(default=None, max_length=200)
    images: list[str] | None = None
    variants: list[ProductVariantPayload] | None = Field(default=None, max_length=50)

    @field_validator("tags")
    @classmethod
    def _tags_max_length(cls, value: list[str] | None) -> list[str] | None:
        for tag in value or []:
            if len(tag) > 40:
                raise ValueError("Cada tag deve ter no máximo 40 caracteres.")
        return value

    @field_validator("images")
    @classmethod
    def _images_must_be_data_urls(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        return _validate_images(value)


class AdjustStockRequest(BaseModel):
    delta: int
    reason: str = Field(min_length=1, max_length=500)


class ProductVariantResponse(BaseModel):
    name: str
    sku: str | None
    barcode: str | None
    price_cents: int | None
    promo_price_cents: int | None
    stock_quantity: int


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
    sku: str | None
    barcode: str | None
    brand: str | None
    supplier: str | None
    category: str | None
    subcategory: str | None
    short_description: str | None
    tags: list[str]
    cost_price_cents: int | None
    promo_price_cents: int | None
    min_stock: int | None
    max_stock: int | None
    stock_location: str | None
    images: list[str]
    variants: list[ProductVariantResponse]
    # Margem calculada no servidor (preço − custo), quando há preço de custo.
    margin_cents: int | None
    margin_pct: float | None
    created_at: datetime
    updated_at: datetime
