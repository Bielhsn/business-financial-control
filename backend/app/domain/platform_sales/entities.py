from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class PlatformSale:
    """Venda/reembolso normalizado, guardado com detalhe suficiente para análise
    (produto, horário, comprador) — diferente do lançamento financeiro, que só
    guarda o valor. Cada conector alimenta esta base durante o sync."""

    id: str
    company_id: str
    provider: str
    external_id: str
    product: str
    amount_cents: int
    occurred_at: datetime
    is_refund: bool
    buyer_name: str | None
    buyer_email: str | None
    created_at: datetime


# --- Resultados de análise (o que a API devolve) ---


@dataclass(frozen=True)
class PlatformMetric:
    provider: str
    gross_cents: int  # soma das vendas (sem reembolsos)
    refunds_cents: int  # soma dos reembolsos
    net_cents: int  # bruto - reembolsos
    orders: int  # nº de vendas
    refunds: int  # nº de reembolsos
    avg_ticket_cents: int  # ticket médio das vendas


@dataclass(frozen=True)
class TopProduct:
    product: str
    quantity: int
    revenue_cents: int


@dataclass(frozen=True)
class PeakHour:
    hour: int  # 0..23
    orders: int


@dataclass(frozen=True)
class SalesAnalytics:
    total_gross_cents: int
    total_refunds_cents: int
    total_net_cents: int
    total_orders: int
    total_refunds: int
    avg_ticket_cents: int
    unique_buyers: int
    by_platform: list[PlatformMetric] = field(default_factory=list)
    top_products: list[TopProduct] = field(default_factory=list)
    peak_hours: list[PeakHour] = field(default_factory=list)
