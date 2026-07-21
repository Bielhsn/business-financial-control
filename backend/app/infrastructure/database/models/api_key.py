from datetime import datetime

from beanie import Document, Indexed


class ApiKeyDocument(Document):
    company_id: Indexed(str)  # type: ignore[valid-type]
    name: str
    prefix: str
    hashed_key: Indexed(str, unique=True)  # type: ignore[valid-type]
    revoked: bool = False
    created_at: datetime
    last_used_at: datetime | None = None

    class Settings:
        name = "api_keys"
