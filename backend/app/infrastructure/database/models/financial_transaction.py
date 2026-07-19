from datetime import datetime

from beanie import Document, Indexed
from pymongo import IndexModel


class FinancialTransactionDocument(Document):
    company_id: Indexed(str)  # type: ignore[valid-type]
    category_id: str
    type: str
    amount_cents: int
    description: str
    status: str
    due_date: datetime | None = None
    paid_at: datetime | None = None
    notes: str | None = None
    client_id: str | None = None
    external_ref: str | None = None
    created_by: str
    created_at: datetime
    updated_at: datetime

    class Settings:
        name = "financial_transactions"
        indexes = [
            IndexModel([("company_id", 1), ("status", 1)]),
            IndexModel([("company_id", 1), ("type", 1), ("status", 1), ("paid_at", 1)]),
            IndexModel([("company_id", 1), ("client_id", 1), ("status", 1)]),
            # Unicidade por empresa+referência externa: o sync de integrações é
            # idempotente e nunca duplica um lançamento já importado.
            IndexModel(
                [("company_id", 1), ("external_ref", 1)],
                unique=True,
                partialFilterExpression={"external_ref": {"$type": "string"}},
            ),
        ]
