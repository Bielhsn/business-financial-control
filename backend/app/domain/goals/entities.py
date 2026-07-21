from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class GoalMetric(StrEnum):
    """Métrica mensal que a meta acompanha."""

    MONTHLY_INCOME = "monthly_income"  # faturamento (receitas do mês)
    MONTHLY_NET = "monthly_net"  # resultado (receitas − despesas)


@dataclass
class FinancialGoal:
    id: str
    company_id: str
    metric: GoalMetric
    target_cents: int
    updated_at: datetime
