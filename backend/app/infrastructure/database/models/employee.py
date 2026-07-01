from datetime import datetime

from beanie import Document, Indexed


class EmployeeDocument(Document):
    company_id: Indexed(str)  # type: ignore[valid-type]
    name: str
    email: str | None = None
    phone: str | None = None
    role_title: str | None = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Settings:
        name = "employees"
