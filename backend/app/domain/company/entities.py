from dataclasses import dataclass, field
from datetime import datetime

from app.domain.company.roles import CompanyRole


@dataclass
class Company:
    id: str
    name: str
    segment: str
    employee_count: int
    average_customer_count: int
    city: str
    state: str
    country: str
    size: str
    tax_regime: str | None
    additional_info: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    # Onboarding 2.0 — defaults mantêm compatibilidade com empresas já criadas.
    currency: str = "BRL"
    sales_channels: list[str] = field(default_factory=list)
    sales_mode: str | None = None
    main_offerings: str | None = None


@dataclass
class CompanyMembership:
    id: str
    company_id: str
    user_id: str
    role: CompanyRole
    created_at: datetime
