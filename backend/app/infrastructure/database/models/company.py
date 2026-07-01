from datetime import datetime

from beanie import Document


class CompanyDocument(Document):
    name: str
    segment: str
    employee_count: int
    average_customer_count: int
    city: str
    state: str
    country: str
    size: str
    tax_regime: str | None = None
    additional_info: str | None = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Settings:
        name = "companies"
