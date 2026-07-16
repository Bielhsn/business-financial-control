from datetime import datetime

from beanie import Document, Indexed


class AppointmentDocument(Document):
    company_id: Indexed(str)  # type: ignore[valid-type]
    title: str
    starts_at: datetime
    duration_minutes: int
    status: str = "scheduled"
    client_id: str | None = None
    client_name: str | None = None
    employee_id: str | None = None
    employee_name: str | None = None
    catalog_item_id: str | None = None
    price_cents: int | None = None
    notes: str | None = None
    revenue_transaction_id: str | None = None
    created_by: str
    created_at: datetime
    updated_at: datetime

    class Settings:
        name = "appointments"
