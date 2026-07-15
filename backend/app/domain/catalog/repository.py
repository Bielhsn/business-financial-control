from typing import Protocol

from app.domain.catalog.entities import CatalogItem, CatalogItemKind, ProductVariant, StockMovement


class CatalogItemRepository(Protocol):
    """Toda implementação filtra/carimba pela empresa do contexto de tenant atual."""

    async def create(
        self,
        *,
        name: str,
        description: str | None,
        price_cents: int,
        kind: CatalogItemKind,
        tracks_inventory: bool,
        stock_quantity: int | None,
        sku: str | None = None,
        barcode: str | None = None,
        brand: str | None = None,
        supplier: str | None = None,
        category: str | None = None,
        subcategory: str | None = None,
        short_description: str | None = None,
        tags: list[str] | None = None,
        cost_price_cents: int | None = None,
        promo_price_cents: int | None = None,
        min_stock: int | None = None,
        max_stock: int | None = None,
        stock_location: str | None = None,
        images: list[str] | None = None,
        variants: list[ProductVariant] | None = None,
    ) -> CatalogItem: ...

    async def get_by_id(self, item_id: str) -> CatalogItem | None: ...

    async def find_by_sku(self, sku: str) -> CatalogItem | None:
        """Busca por SKU dentro da empresa atual — usada para garantir unicidade."""
        ...

    async def list_all(self, *, only_active: bool = True) -> list[CatalogItem]: ...

    async def update(self, item_id: str, **fields: object) -> CatalogItem | None: ...

    async def adjust_stock(self, item_id: str, *, delta: int) -> CatalogItem | None:
        """Incrementa/decrementa o estoque atomicamente (`$inc`), evitando condições
        de corrida entre leitura e escrita em ajustes concorrentes."""
        ...


class StockMovementRepository(Protocol):
    async def create(
        self, *, item_id: str, delta: int, reason: str, created_by: str
    ) -> StockMovement: ...

    async def list_for_item(self, item_id: str) -> list[StockMovement]: ...
