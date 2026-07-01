from typing import Protocol

from app.domain.catalog.entities import CatalogItem, CatalogItemKind, StockMovement


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
    ) -> CatalogItem: ...

    async def get_by_id(self, item_id: str) -> CatalogItem | None: ...

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
