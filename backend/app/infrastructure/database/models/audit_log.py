from datetime import datetime

import pymongo
from beanie import Document


class AuditLogDocument(Document):
    company_id: str
    user_id: str | None = None
    action: str
    details: dict[str, object] = {}
    created_at: datetime

    class Settings:
        name = "audit_logs"
        indexes = [
            [("company_id", pymongo.ASCENDING), ("created_at", pymongo.DESCENDING)],
        ]
