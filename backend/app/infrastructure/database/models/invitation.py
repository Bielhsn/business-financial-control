from datetime import datetime

from beanie import Document, Indexed
from pymongo import IndexModel


class InvitationDocument(Document):
    company_id: Indexed(str)  # type: ignore[valid-type]
    email: str
    role: str
    token: Indexed(str, unique=True)  # type: ignore[valid-type]
    status: str = "pending"
    invited_by: str
    expires_at: datetime
    created_at: datetime

    class Settings:
        name = "invitations"
        indexes = [
            IndexModel([("company_id", 1), ("email", 1), ("status", 1)]),
        ]
