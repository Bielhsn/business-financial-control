from datetime import datetime

from beanie import Document, Indexed


class CatalogItemDocument(Document):
    company_id: Indexed(str)  # type: ignore[valid-type]
    name: str
    description: str | None = None
    price_cents: int
    kind: str
    tracks_inventory: bool = False
    stock_quantity: int | None = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Settings:
        name = "catalog_items"
