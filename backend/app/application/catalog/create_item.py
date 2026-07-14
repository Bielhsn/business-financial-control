from app.core.exceptions import ValidationError
from app.domain.catalog.entities import CatalogItem, CatalogItemKind
from app.domain.catalog.repository import CatalogItemRepository


class CreateCatalogItemUseCase:
    def __init__(self, item_repository: CatalogItemRepository) -> None:
        self._item_repository = item_repository

    async def execute(
        self,
        *,
        name: str,
        description: str | None,
        price_cents: int,
        kind: CatalogItemKind,
        tracks_inventory: bool,
        stock_quantity: int | None,
    ) -> CatalogItem:
        if price_cents <= 0:
            raise ValidationError("O preço deve ser maior que zero.")

        if kind == CatalogItemKind.SERVICE:
            if tracks_inventory:
                raise ValidationError("Serviços não controlam estoque.")
            stock_quantity = None
        elif tracks_inventory:
            stock_quantity = stock_quantity if stock_quantity is not None else 0
            if stock_quantity < 0:
                raise ValidationError("O estoque inicial não pode ser negativo.")
        else:
            stock_quantity = None

        return await self._item_repository.create(
            name=name.strip(),
            description=description.strip() if description else None,
            price_cents=price_cents,
            kind=kind,
            tracks_inventory=tracks_inventory,
            stock_quantity=stock_quantity,
        )
