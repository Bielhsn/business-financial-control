from datetime import datetime

from beanie import Document, Indexed
from pymongo import IndexModel


class RecurringTransactionDocument(Document):
    company_id: Indexed(str)  # type: ignore[valid-type]
    category_id: str
    type: str
    amount_cents: int
    description: str
    frequency: str
    anchor_day: int
    next_run_date: datetime
    active: bool = True
    notes: str | None = None
    client_id: str | None = None
    created_by: str
    created_at: datetime
    updated_at: datetime
    last_run_at: datetime | None = None

    class Settings:
        name = "recurring_transactions"
        indexes = [
            IndexModel([("company_id", 1), ("active", 1), ("next_run_date", 1)]),
        ]
