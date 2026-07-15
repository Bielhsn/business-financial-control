from dataclasses import dataclass
from enum import StrEnum


class SignalKind(StrEnum):
    STOCK_ZERO = "stock_zero"
    STOCK_LOW = "stock_low"
    LOW_MARGIN = "low_margin"
    REVENUE_DROP = "revenue_drop"
    OVERDUE_BILLS = "overdue_bills"


class SignalSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class BusinessSignal:
    """Um sinal de negócio **computado deterministicamente** pela aplicação.

    A IA nunca calcula sinais — ela só recebe esta lista pronta e narra
    recomendações em cima dela (mesma divisão interpretação × cálculo dos
    insights financeiros)."""

    kind: SignalKind
    severity: SignalSeverity
    title: str
    detail: str
