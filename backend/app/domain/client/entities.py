from dataclasses import dataclass
from datetime import datetime


@dataclass
class Client:
    id: str
    company_id: str
    name: str
    email: str | None
    phone: str | None
    notes: str | None
    custom_fields: dict[str, str]
    is_active: bool
    created_at: datetime
    updated_at: datetime


@dataclass
class ClientSummary:
    client_id: str
    total_spent_cents: int
    purchase_count: int
    last_purchase_at: datetime | None
