"""DRE simplificado do mês (Demonstrativo de Resultado) com comparativo contra o
mês anterior.

Agrupa os lançamentos **pagos** do mês por categoria (receitas e despesas),
soma os totais e o resultado (receitas − despesas), e compara com o mês
anterior. A parte de agrupamento é uma função pura, testável com primitivos; o
caso de uso apenas busca os períodos e monta o comparativo.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.domain.financial.entities import FinancialCategoryType, FinancialTransaction
from app.domain.financial.repository import (
    FinancialCategoryRepository,
    FinancialTransactionRepository,
)


@dataclass
class StatementLine:
    category_id: str
    category_name: str
    amount_cents: int


@dataclass
class IncomeStatement:
    income_lines: list[StatementLine] = field(default_factory=list)
    expense_lines: list[StatementLine] = field(default_factory=list)
    total_income_cents: int = 0
    total_expense_cents: int = 0
    net_result_cents: int = 0


@dataclass
class IncomeStatementComparison:
    year: int
    month: int
    current: IncomeStatement
    previous_income_cents: int
    previous_expense_cents: int
    previous_net_result_cents: int
    income_change_pct: float | None
    expense_change_pct: float | None
    net_change_pct: float | None


def compute_income_statement(
    transactions: list[FinancialTransaction], category_names: dict[str, str]
) -> IncomeStatement:
    income: dict[str, int] = {}
    expense: dict[str, int] = {}

    for transaction in transactions:
        bucket = income if transaction.type == FinancialCategoryType.INCOME else expense
        bucket[transaction.category_id] = (
            bucket.get(transaction.category_id, 0) + transaction.amount_cents
        )

    income_lines = _to_lines(income, category_names)
    expense_lines = _to_lines(expense, category_names)
    total_income = sum(line.amount_cents for line in income_lines)
    total_expense = sum(line.amount_cents for line in expense_lines)

    return IncomeStatement(
        income_lines=income_lines,
        expense_lines=expense_lines,
        total_income_cents=total_income,
        total_expense_cents=total_expense,
        net_result_cents=total_income - total_expense,
    )


def _to_lines(totals: dict[str, int], category_names: dict[str, str]) -> list[StatementLine]:
    lines = [
        StatementLine(
            category_id=category_id,
            category_name=category_names.get(category_id, "Sem categoria"),
            amount_cents=amount,
        )
        for category_id, amount in totals.items()
    ]
    # Maiores valores primeiro — o que mais pesa no resultado aparece no topo.
    lines.sort(key=lambda line: line.amount_cents, reverse=True)
    return lines


def _change_pct(current: int, previous: int) -> float | None:
    if previous == 0:
        return None
    return round((current - previous) / previous * 100, 1)


def month_bounds(year: int, month: int) -> tuple[datetime, datetime]:
    start = datetime(year, month, 1, tzinfo=UTC)
    if month == 12:
        end = datetime(year + 1, 1, 1, tzinfo=UTC)
    else:
        end = datetime(year, month + 1, 1, tzinfo=UTC)
    return start, end


def previous_month(year: int, month: int) -> tuple[int, int]:
    if month == 1:
        return year - 1, 12
    return year, month - 1


class GetIncomeStatementUseCase:
    def __init__(
        self,
        transaction_repository: FinancialTransactionRepository,
        category_repository: FinancialCategoryRepository,
    ) -> None:
        self._transactions = transaction_repository
        self._categories = category_repository

    async def execute(self, *, year: int, month: int) -> IncomeStatementComparison:
        categories = await self._categories.list_all(only_active=False)
        category_names = {category.id: category.name for category in categories}

        start, end = month_bounds(year, month)
        prev_year, prev_month = previous_month(year, month)
        prev_start, prev_end = month_bounds(prev_year, prev_month)

        current_tx = await self._transactions.list_paid_between(start=start, end=end)
        previous_tx = await self._transactions.list_paid_between(start=prev_start, end=prev_end)

        current = compute_income_statement(current_tx, category_names)
        previous = compute_income_statement(previous_tx, category_names)

        return IncomeStatementComparison(
            year=year,
            month=month,
            current=current,
            previous_income_cents=previous.total_income_cents,
            previous_expense_cents=previous.total_expense_cents,
            previous_net_result_cents=previous.net_result_cents,
            income_change_pct=_change_pct(current.total_income_cents, previous.total_income_cents),
            expense_change_pct=_change_pct(
                current.total_expense_cents, previous.total_expense_cents
            ),
            net_change_pct=_change_pct(current.net_result_cents, previous.net_result_cents),
        )
