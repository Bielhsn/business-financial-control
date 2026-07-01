from datetime import datetime

from beanie import Document, Indexed
from pymongo import IndexModel


class CompanyMembershipDocument(Document):
    company_id: Indexed(str)  # type: ignore[valid-type]
    user_id: Indexed(str)  # type: ignore[valid-type]
    role: str
    created_at: datetime

    class Settings:
        name = "company_memberships"
        indexes = [
            IndexModel([("user_id", 1), ("company_id", 1)], unique=True),
        ]
