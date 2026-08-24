from datetime import datetime

from beanie import Document
from pymongo import IndexModel


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
    # Mensagem de retorno enviada por WhatsApp (marcadores {nome}/{empresa}/{dias}).
    client_return_message: str | None = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Settings:
        name = "companies"
        indexes = [
            # Um CNPJ pertence a uma empresa só. A verificação em código não
            # basta: duas requisições simultâneas passam pelo "já existe?" antes
            # de qualquer uma gravar, e as duas gravam. Só o banco resolve isso.
            #
            # Parcial porque o campo é opcional — sem o filtro, todas as
            # empresas sem CNPJ colidiriam entre si no valor null.
            IndexModel(
                [("cnpj", 1)],
                unique=True,
                name="uniq_company_cnpj",
                partialFilterExpression={"cnpj": {"$type": "string"}},
            ),
        ]
