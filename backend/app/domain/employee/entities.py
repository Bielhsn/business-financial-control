from dataclasses import dataclass
from datetime import datetime


@dataclass
class Employee:
    id: str
    company_id: str
    name: str
    email: str | None
    phone: str | None
    role_title: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
