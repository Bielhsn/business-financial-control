from dataclasses import dataclass
from enum import StrEnum


class KPIUnit(StrEnum):
    CENTS = "cents"
    PERCENTAGE = "percentage"
    COUNT = "count"


class KPIMetric(StrEnum):
    TOTAL_REVENUE = "total_revenue"
    TOTAL_EXPENSES = "total_expenses"
    PROFIT = "profit"
    PROFIT_MARGIN = "profit_margin"
    AVERAGE_TICKET = "average_ticket"
    TRANSACTION_COUNT = "transaction_count"
    ACTIVE_CLIENTS = "active_clients"


@dataclass(frozen=True)
class KPIMetricDefinition:
    metric: KPIMetric
    unit: KPIUnit
    description: str


KPI_METRIC_REGISTRY: tuple[KPIMetricDefinition, ...] = (
    KPIMetricDefinition(
        KPIMetric.TOTAL_REVENUE, KPIUnit.CENTS, "Soma das receitas pagas no período."
    ),
    KPIMetricDefinition(
        KPIMetric.TOTAL_EXPENSES, KPIUnit.CENTS, "Soma das despesas pagas no período."
    ),
    KPIMetricDefinition(KPIMetric.PROFIT, KPIUnit.CENTS, "Receita menos despesas do período."),
    KPIMetricDefinition(
        KPIMetric.PROFIT_MARGIN,
        KPIUnit.PERCENTAGE,
        "Lucro dividido pela receita do período.",
    ),
    KPIMetricDefinition(
        KPIMetric.AVERAGE_TICKET,
        KPIUnit.CENTS,
        "Valor médio dos lançamentos de receita pagos no período.",
    ),
    KPIMetricDefinition(
        KPIMetric.TRANSACTION_COUNT,
        KPIUnit.COUNT,
        "Quantidade de lançamentos pagos no período.",
    ),
    KPIMetricDefinition(
        KPIMetric.ACTIVE_CLIENTS,
        KPIUnit.COUNT,
        "Quantidade de clientes distintos com compras pagas no período.",
    ),
)

KPI_METRIC_IDS: frozenset[str] = frozenset(
    definition.metric.value for definition in KPI_METRIC_REGISTRY
)


def get_kpi_metric_unit(metric: KPIMetric) -> KPIUnit:
    return next(d.unit for d in KPI_METRIC_REGISTRY if d.metric == metric)
