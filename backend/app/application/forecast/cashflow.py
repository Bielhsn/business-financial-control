"""Previsão de fluxo de caixa a partir do histórico mensal de lançamentos pagos.

Método determinístico e explicável:
- Mês corrente: run-rate (líquido realizado ÷ dias decorridos × dias do mês).
- Próximos meses: média dos meses fechados (janela curta), com uma tendência
  calculada comparando a metade antiga com a metade recente do histórico.
"""

import calendar
from datetime import UTC, datetime

from app.domain.financial.entities import FinancialCategoryType, FinancialTransaction
from app.domain.financial.repository import FinancialTransactionRepository
from app.domain.forecast.entities import CashflowForecast, MonthPoint

_HISTORY_MONTHS = 6  # meses fechados considerados no histórico
_AVG_WINDOW = 3  # meses fechados usados na projeção do próximo mês


def _add_months(year: int, month: int, delta: int) -> tuple[int, int]:
    index = (month - 1) + delta
    return year + index // 12, index % 12 + 1


def _bucket(transactions: list[FinancialTransaction], year: int, month: int) -> MonthPoint:
    income = expense = 0
    for tx in transactions:
        if tx.paid_at is None:
            continue
        paid = tx.paid_at
        if paid.year != year or paid.month != month:
            continue
        if tx.type == FinancialCategoryType.INCOME:
            income += tx.amount_cents
        else:
            expense += tx.amount_cents
    return MonthPoint(year=year, month=month, income_cents=income, expense_cents=expense)


def _trend_pct(nets: list[int]) -> float | None:
    """Variação % entre a média da metade antiga e a da metade recente."""
    if len(nets) < 2:
        return None
    half = len(nets) // 2
    older = nets[:half]
    recent = nets[half:]
    old_avg = sum(older) / len(older)
    new_avg = sum(recent) / len(recent)
    if old_avg == 0:
        return None
    return round(((new_avg - old_avg) / abs(old_avg)) * 100, 2)


def compute_forecast(
    *, history: list[MonthPoint], current: MonthPoint, days_elapsed: int, days_in_month: int
) -> CashflowForecast:
    actual = current.net_cents

    # Run-rate do mês corrente (nunca projeta menos que o já realizado).
    if days_elapsed <= 0:
        projected_current = actual
    else:
        projected_current = round(actual / days_elapsed * days_in_month)

    closed_nets = [point.net_cents for point in history]
    if closed_nets:
        window = closed_nets[-_AVG_WINDOW:]
        next_projection = round(sum(window) / len(window))
    else:
        next_projection = projected_current

    return CashflowForecast(
        current_month_actual_net_cents=actual,
        current_month_projected_net_cents=projected_current,
        next_month_projected_net_cents=next_projection,
        trend_pct=_trend_pct(closed_nets),
        method="run-rate + média dos meses fechados",
        history=history,
    )


class GetCashflowForecastUseCase:
    def __init__(self, transaction_repository: FinancialTransactionRepository) -> None:
        self._transactions = transaction_repository

    async def execute(self, *, now: datetime | None = None) -> CashflowForecast:
        moment = now or datetime.now(UTC)
        # Janela: início do mês mais antigo do histórico até o fim do mês corrente.
        start_year, start_month = _add_months(moment.year, moment.month, -_HISTORY_MONTHS)
        start = datetime(start_year, start_month, 1, tzinfo=UTC)
        end = moment

        transactions = await self._transactions.list_paid_between(start=start, end=end)

        history: list[MonthPoint] = []
        for delta in range(-_HISTORY_MONTHS, 0):
            year, month = _add_months(moment.year, moment.month, delta)
            history.append(_bucket(transactions, year, month))

        current = _bucket(transactions, moment.year, moment.month)
        days_in_month = calendar.monthrange(moment.year, moment.month)[1]
        return compute_forecast(
            history=history,
            current=current,
            days_elapsed=moment.day,
            days_in_month=days_in_month,
        )
