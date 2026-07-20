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
    # Branding por empresa (white-label light): aplicado no shell do frontend.
    brand_logo: str | None = None  # data URL (image/*), tamanho limitado no schema
    brand_primary_color: str | None = None  # hex #RRGGBB
    brand_theme: str | None = None  # "light" | "dark" (tema padrão da empresa)
    # Cadastro fiscal/institucional completo (Etapa 26) — todos opcionais para não
    # quebrar empresas já criadas; preenchíveis manualmente ou via consulta de CNPJ.
    legal_name: str | None = None  # Razão Social
    trade_name: str | None = None  # Nome Fantasia
    cnpj: str | None = None  # apenas dígitos (14)
    subsegment: str | None = None
    monthly_revenue_cents: int | None = None  # faturamento médio mensal
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    social_links: dict[str, str] = field(default_factory=dict)


@dataclass
class CompanyMembership:
    id: str
    company_id: str
    user_id: str
    role: CompanyRole
    created_at: datetime
