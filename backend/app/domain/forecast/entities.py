from dataclasses import dataclass, field


@dataclass(frozen=True)
class MonthPoint:
    year: int
    month: int  # 1..12
    income_cents: int
    expense_cents: int

    @property
    def net_cents(self) -> int:
        return self.income_cents - self.expense_cents


@dataclass(frozen=True)
class CashflowForecast:
    """Projeção de fluxo de caixa. Determinística e explicável — nada de caixa
    preta: o mês corrente é projetado por run-rate (ritmo até agora), e os
    próximos meses pela tendência dos meses fechados."""

    current_month_actual_net_cents: int
    current_month_projected_net_cents: int
    next_month_projected_net_cents: int
    trend_pct: float | None  # variação % entre a metade antiga e a recente do histórico
    method: str  # descrição curta do método (para exibir/transparência)
    history: list[MonthPoint] = field(default_factory=list)
