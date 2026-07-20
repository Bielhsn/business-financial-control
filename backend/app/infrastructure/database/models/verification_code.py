from datetime import datetime

from beanie import Document, Indexed
from pymongo import IndexModel


class VerificationCodeDocument(Document):
    user_id: Indexed(str)  # type: ignore[valid-type]
    purpose: str
    code_hash: str
    expires_at: datetime
    used: bool = False
    created_at: datetime

    class Settings:
        name = "verification_codes"
        indexes = [
            IndexModel([("user_id", 1), ("purpose", 1), ("used", 1)]),
            # TTL: o Mongo remove documentos expirados sozinho (limpeza automática).
            IndexModel([("expires_at", 1)], expireAfterSeconds=0),
        ]
