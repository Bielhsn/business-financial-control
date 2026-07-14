from datetime import datetime

from beanie import Document, Indexed


class ClientDocument(Document):
    company_id: Indexed(str)  # type: ignore[valid-type]
    name: str
    email: str | None = None
    phone: str | None = None
    notes: str | None = None
    custom_fields: dict[str, str] = {}
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Settings:
        name = "clients"
