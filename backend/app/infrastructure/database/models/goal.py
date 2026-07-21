from datetime import datetime

from beanie import Document, Indexed
from pymongo import IndexModel


class GoalDocument(Document):
    company_id: Indexed(str)  # type: ignore[valid-type]
    metric: str
    target_cents: int
    updated_at: datetime

    class Settings:
        name = "goals"
        indexes = [
            IndexModel([("company_id", 1), ("metric", 1)], unique=True),
        ]
