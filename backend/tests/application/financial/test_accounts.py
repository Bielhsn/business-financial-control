from datetime import UTC, datetime

from app.application.financial.accounts import compute_accounts
from app.domain.financial.entities import (
    FinancialCategoryType,
    FinancialTransaction,
    TransactionStatus,
)

_TODAY = datetime(2026, 7, 20, tzinfo=UTC)


def _tx(
    tx_id: str,
    *,
    type: FinancialCategoryType,
    amount_cents: int,
    due_date: datetime | None,
    status: TransactionStatus = TransactionStatus.PENDING,
) -> FinancialTransaction:
    now = datetime(2026, 7, 1, tzinfo=UTC)
    return FinancialTransaction(
        id=tx_id,
        company_id="company-1",
        category_id="cat",
        type=type,
        amount_cents=amount_cents,
        description=f"Lançamento {tx_id}",
        status=status,
        due_date=due_date,
        paid_at=None,
        notes=None,
        client_id=None,
        created_by="u",
        created_at=now,
        updated_at=now,
    )


def test_classifies_overdue_due_soon_and_upcoming() -> None:
    transactions = [
        _tx(
            "a",
            type=FinancialCategoryType.EXPENSE,
            amount_cents=1000,
            due_date=datetime(2026, 7, 10, tzinfo=UTC),
        ),  # vencido
        _tx(
            "b",
            type=FinancialCategoryType.EXPENSE,
            amount_cents=2000,
            due_date=datetime(2026, 7, 22, tzinfo=UTC),
        ),  # a vencer (2 dias)
        _tx(
            "c",
            type=FinancialCategoryType.EXPENSE,
            amount_cents=4000,
            due_date=datetime(2026, 8, 30, tzinfo=UTC),
        ),  # futuro
        _tx(
            "d", type=FinancialCategoryType.EXPENSE, amount_cents=500, due_date=None
        ),  # sem data → futuro
    ]

    summary = compute_accounts(transactions, today=_TODAY)

    payable = summary.payable
    assert payable.overdue_cents == 1000
    assert payable.due_soon_cents == 2000
    assert payable.upcoming_cents == 4500
    assert payable.total_cents == 7500
    assert summary.receivable.total_cents == 0


def test_splits_payable_and_receivable_and_flags_overdue() -> None:
    transactions = [
        _tx(
            "in",
            type=FinancialCategoryType.INCOME,
            amount_cents=9000,
            due_date=datetime(2026, 7, 5, tzinfo=UTC),
        ),
        _tx(
            "ex",
            type=FinancialCategoryType.EXPENSE,
            amount_cents=3000,
            due_date=datetime(2026, 7, 25, tzinfo=UTC),
        ),
    ]

    summary = compute_accounts(transactions, today=_TODAY)

    assert summary.receivable.total_cents == 9000
    assert summary.receivable.overdue_cents == 9000
    receivable_item = summary.receivable.items[0]
    assert receivable_item.is_overdue is True
    assert receivable_item.days_until_due == -15
    assert summary.payable.items[0].is_overdue is False


def test_ignores_non_pending_and_sorts_by_due_date() -> None:
    transactions = [
        _tx(
            "paid",
            type=FinancialCategoryType.EXPENSE,
            amount_cents=1000,
            due_date=datetime(2026, 7, 1, tzinfo=UTC),
            status=TransactionStatus.PAID,
        ),
        _tx(
            "later",
            type=FinancialCategoryType.EXPENSE,
            amount_cents=1000,
            due_date=datetime(2026, 8, 1, tzinfo=UTC),
        ),
        _tx("nodate", type=FinancialCategoryType.EXPENSE, amount_cents=1000, due_date=None),
        _tx(
            "sooner",
            type=FinancialCategoryType.EXPENSE,
            amount_cents=1000,
            due_date=datetime(2026, 7, 10, tzinfo=UTC),
        ),
    ]

    summary = compute_accounts(transactions, today=_TODAY)

    # "paid" é ignorado; ordena por vencimento com "sem data" por último.
    assert [item.id for item in summary.payable.items] == ["sooner", "later", "nodate"]
    assert summary.payable.total_cents == 3000
