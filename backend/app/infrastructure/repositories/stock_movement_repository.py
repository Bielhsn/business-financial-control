from datetime import UTC, datetime

from app.core.tenant import get_current_company_id
from app.domain.catalog.entities import StockMovement
from app.infrastructure.database.models.stock_movement import StockMovementDocument


def _to_entity(document: StockMovementDocument) -> StockMovement:
    return StockMovement(
        id=str(document.id),
        company_id=document.company_id,
        item_id=document.item_id,
        delta=document.delta,
        reason=document.reason,
        created_by=document.created_by,
        created_at=document.created_at,
    )


class BeanieStockMovementRepository:
    async def create(
        self, *, item_id: str, delta: int, reason: str, created_by: str
    ) -> StockMovement:
        document = StockMovementDocument(
            company_id=get_current_company_id(),
            item_id=item_id,
            delta=delta,
            reason=reason,
            created_by=created_by,
            created_at=datetime.now(UTC),
        )
        await document.insert()
        return _to_entity(document)

    async def list_for_item(self, item_id: str) -> list[StockMovement]:
        documents = await StockMovementDocument.find(
            StockMovementDocument.company_id == get_current_company_id(),
            StockMovementDocument.item_id == item_id,
        ).to_list()
        return [_to_entity(document) for document in documents]
