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
    currency: str = "BRL"
    sales_channels: list[str] = []
    sales_mode: str | None = None
    main_offerings: str | None = None
    brand_logo: str | None = None
    brand_primary_color: str | None = None
    brand_theme: str | None = None
    legal_name: str | None = None
    trade_name: str | None = None
    cnpj: str | None = None
    subsegment: str | None = None
    monthly_revenue_cents: int | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    social_links: dict[str, str] = {}
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Settings:
        name = "companies"
