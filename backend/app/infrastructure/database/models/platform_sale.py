from datetime import datetime

from beanie import Document, Indexed
from pymongo import IndexModel


class PlatformSaleDocument(Document):
    company_id: Indexed(str)  # type: ignore[valid-type]
    provider: str
    external_id: str
    product: str
    amount_cents: int
    occurred_at: datetime
    is_refund: bool = False
    buyer_name: str | None = None
    buyer_email: str | None = None
    created_at: datetime

    class Settings:
        name = "platform_sales"
        indexes = [
            IndexModel([("company_id", 1), ("occurred_at", -1)]),
            # Idempotência: uma venda (provider+external_id) nunca duplica por empresa.
            IndexModel(
                [("company_id", 1), ("provider", 1), ("external_id", 1)],
                unique=True,
            ),
        ]
