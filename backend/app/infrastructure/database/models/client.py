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
    # Retorno de clientes (cadência esperada e data do último atendimento).
    return_interval_days: int | None = None
    last_visit_at: datetime | None = None

    class Settings:
        name = "clients"
