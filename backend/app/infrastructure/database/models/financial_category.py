from datetime import datetime

from beanie import Document, Indexed
from pymongo import IndexModel


class FinancialCategoryDocument(Document):
    company_id: Indexed(str)  # type: ignore[valid-type]
    name: str
    type: str
    is_active: bool = True
    created_at: datetime

    class Settings:
        name = "financial_categories"
        indexes = [
            IndexModel([("company_id", 1), ("name", 1), ("type", 1)], unique=True),
        ]
