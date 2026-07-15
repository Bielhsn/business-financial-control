from datetime import datetime

from beanie import Document, Indexed
from pydantic import BaseModel


class ProductVariantModel(BaseModel):
    """Variação embutida no documento do item — não é coleção própria porque
    variações só existem no contexto do produto pai (sem consultas isoladas)."""

    name: str
    sku: str | None = None
    barcode: str | None = None
    price_cents: int | None = None
    promo_price_cents: int | None = None
    stock_quantity: int = 0


class CatalogItemDocument(Document):
    company_id: Indexed(str)  # type: ignore[valid-type]
    name: str
    description: str | None = None
    price_cents: int
    kind: str
    tracks_inventory: bool = False
    stock_quantity: int | None = None
    is_active: bool = True
    # Catálogo 2.0 — todos com default para que documentos antigos carreguem
    # sem migração.
    sku: str | None = None
    barcode: str | None = None
    brand: str | None = None
    supplier: str | None = None
    category: str | None = None
    subcategory: str | None = None
    short_description: str | None = None
    tags: list[str] = []
    cost_price_cents: int | None = None
    promo_price_cents: int | None = None
    min_stock: int | None = None
    max_stock: int | None = None
    stock_location: str | None = None
    images: list[str] = []
    variants: list[ProductVariantModel] = []
    created_at: datetime
    updated_at: datetime

    class Settings:
        name = "catalog_items"
