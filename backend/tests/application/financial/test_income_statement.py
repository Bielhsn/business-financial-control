from datetime import UTC, datetime

from app.application.financial.income_statement import (
    compute_income_statement,
    month_bounds,
    previous_month,
)
from app.domain.financial.entities import (
    FinancialCategoryType,
    FinancialTransaction,
    TransactionStatus,
)

_NAMES = {"c1": "Vendas", "c2": "Serviços", "e1": "Aluguel", "e2": "Salários"}


def _tx(category_id: str, type: FinancialCategoryType, amount_cents: int) -> FinancialTransaction:
    now = datetime(2026, 7, 1, tzinfo=UTC)
    return FinancialTransaction(
        id=f"tx-{category_id}-{amount_cents}",
        company_id="company-1",
        category_id=category_id,
        type=type,
        amount_cents=amount_cents,
        description="x",
        status=TransactionStatus.PAID,
        due_date=None,
        paid_at=now,
        notes=None,
        client_id=None,
        created_by="u",
        created_at=now,
        updated_at=now,
    )


def test_groups_by_category_and_computes_result() -> None:
    transactions = [
        _tx("c1", FinancialCategoryType.INCOME, 10000),
        _tx("c1", FinancialCategoryType.INCOME, 5000),
        _tx("c2", FinancialCategoryType.INCOME, 3000),
        _tx("e1", FinancialCategoryType.EXPENSE, 4000),
        _tx("e2", FinancialCategoryType.EXPENSE, 6000),
    ]

    statement = compute_income_statement(transactions, _NAMES)

    assert statement.total_income_cents == 18000
    assert statement.total_expense_cents == 10000
    assert statement.net_result_cents == 8000
    # Vendas (15000) somou as duas e aparece antes de Serviços (3000).
    assert statement.income_lines[0].category_name == "Vendas"
    assert statement.income_lines[0].amount_cents == 15000
    # Despesas ordenadas pela maior (Salários 6000 antes de Aluguel 4000).
    assert [line.category_name for line in statement.expense_lines] == ["Salários", "Aluguel"]


def test_unknown_category_falls_back_to_label() -> None:
    statement = compute_income_statement([_tx("ghost", FinancialCategoryType.EXPENSE, 100)], {})
    assert statement.expense_lines[0].category_name == "Sem categoria"


def test_month_bounds_and_previous_month_handle_year_rollover() -> None:
    start, end = month_bounds(2026, 12)
    assert start == datetime(2026, 12, 1, tzinfo=UTC)
    assert end == datetime(2027, 1, 1, tzinfo=UTC)
    assert previous_month(2026, 1) == (2025, 12)
    assert previous_month(2026, 7) == (2026, 6)
