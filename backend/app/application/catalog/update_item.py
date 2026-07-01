from app.core.exceptions import NotFoundError, ValidationError
from app.domain.catalog.entities import CatalogItem
from app.domain.catalog.repository import CatalogItemRepository


class UpdateCatalogItemUseCase:
    """Não altera `stock_quantity` diretamente — ajustes de estoque passam por
    `AdjustStockUseCase`, para manter o registro de auditoria (`StockMovement`)."""

    def __init__(self, item_repository: CatalogItemRepository) -> None:
        self._item_repository = item_repository

    async def execute(self, *, item_id: str, **fields: object) -> CatalogItem:
        clean_fields = {key: value for key, value in fields.items() if value is not None}

        price_cents = clean_fields.get("price_cents")
        if isinstance(price_cents, int) and price_cents <= 0:
            raise ValidationError("O preço deve ser maior que zero.")

        if not clean_fields:
            item = await self._item_repository.get_by_id(item_id)
            if item is None:
                raise NotFoundError("Item de catálogo não encontrado.")
            return item

        item = await self._item_repository.update(item_id, **clean_fields)
        if item is None:
            raise NotFoundError("Item de catálogo não encontrado.")
        return item
