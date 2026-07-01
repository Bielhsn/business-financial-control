from datetime import datetime

from beanie import Document, Indexed


class StockMovementDocument(Document):
    company_id: Indexed(str)  # type: ignore[valid-type]
    item_id: Indexed(str)  # type: ignore[valid-type]
    delta: int
    reason: str
    created_by: str
    created_at: datetime

    class Settings:
        name = "stock_movements"
