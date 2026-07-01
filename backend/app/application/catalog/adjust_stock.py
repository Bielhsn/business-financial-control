from app.core.exceptions import NotFoundError, ValidationError
from app.domain.catalog.entities import CatalogItem
from app.domain.catalog.repository import CatalogItemRepository, StockMovementRepository


class AdjustStockUseCase:
    """Validação de estoque negativo feita com base na leitura mais recente do item.

    Sob ajustes concorrentes há uma janela de corrida entre essa leitura e o
    `$inc` atômico no repositório — aceitável para o volume de uma única empresa
    nesta etapa; um cenário de alta concorrência exigiria um `find_one_and_update`
    com filtro condicional (`stock_quantity + delta >= 0`) em uma única operação.
    """

    def __init__(
        self,
        item_repository: CatalogItemRepository,
        movement_repository: StockMovementRepository,
    ) -> None:
        self._item_repository = item_repository
        self._movement_repository = movement_repository

    async def execute(
        self, *, item_id: str, delta: int, reason: str, created_by: str
    ) -> CatalogItem:
        if delta == 0:
            raise ValidationError("O ajuste de estoque não pode ser zero.")

        item = await self._item_repository.get_by_id(item_id)
        if item is None or not item.is_active:
            raise NotFoundError("Item de catálogo não encontrado.")
        if not item.tracks_inventory:
            raise ValidationError("Este item não controla estoque.")

        current_quantity = item.stock_quantity or 0
        if current_quantity + delta < 0:
            raise ValidationError("Estoque insuficiente para este ajuste.")

        updated = await self._item_repository.adjust_stock(item_id, delta=delta)
        assert updated is not None

        await self._movement_repository.create(
            item_id=item_id, delta=delta, reason=reason.strip(), created_by=created_by
        )
        return updated
