"""Modelos de leitura e agregados do painel administrativo do SaaS.

São modelos "achatados" (read models) e resultados de agregação usados apenas
pelo super-admin. Nenhum deles é escopado por empresa — o painel enxerga toda a
plataforma.
"""

from dataclasses import dataclass, field
from datetime import datetime

from app.domain.subscription.entities import SubscriptionStatus
from app.domain.subscription.plans import PlanTier


@dataclass(frozen=True)
class CompanySummary:
    id: str
    name: str
    segment: str
    is_active: bool
    created_at: datetime


@dataclass(frozen=True)
class ConnectionSummary:
    provider: str
    status: str  # connected / error / ...


@dataclass(frozen=True)
class FinancialTotals:
    income_cents: int
    expense_cents: int


# --- Agregados calculados (o que a API devolve) ---


@dataclass(frozen=True)
class RevenueMetrics:
    mrr_cents: int  # receita recorrente mensal (assinaturas ativas)
    arr_cents: int  # receita recorrente anual (MRR × 12)
    active_paying: int  # nº de assinaturas pagas ativas
    trials: int  # assinaturas em teste
    platform_gmv_cents: int  # volume total transacionado pelas empresas (receitas)
    platform_expenses_cents: int  # despesas lançadas pelas empresas


@dataclass(frozen=True)
class CustomerMetrics:
    total_companies: int
    active_companies: int
    inactive_companies: int
    new_this_month: int
    churned: int  # assinaturas canceladas
    churn_rate_pct: float  # canceladas / (ativas pagas + canceladas)


@dataclass(frozen=True)
class SegmentMetric:
    segment: str
    company_count: int


@dataclass(frozen=True)
class PlanBreakdown:
    tier: PlanTier
    subscribers: int
    mrr_cents: int


@dataclass(frozen=True)
class SubscriptionMetrics:
    by_status: dict[SubscriptionStatus, int]
    by_plan: list[PlanBreakdown]
    past_due: int  # inadimplentes


@dataclass(frozen=True)
class SystemMetrics:
    total_users: int
    total_companies: int
    total_connections: int
    connections_with_error: int


@dataclass(frozen=True)
class AdminOverview:
    revenue: RevenueMetrics
    customers: CustomerMetrics
    segments: list[SegmentMetric] = field(default_factory=list)
    subscriptions: SubscriptionMetrics | None = None
    system: SystemMetrics | None = None
