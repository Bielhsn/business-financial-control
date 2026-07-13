from datetime import UTC, datetime

import pytest

from app.application.financial.import_transactions import ImportRow, ImportTransactionsUseCase
from app.domain.financial.entities import FinancialCategoryType, TransactionStatus
from tests.fakes import FakeFinancialCategoryRepository, FakeFinancialTransactionRepository

pytestmark = pytest.mark.anyio


def _row(**overrides: object) -> ImportRow:
    defaults: dict = {
        "date": datetime(2026, 6, 15, tzinfo=UTC),
        "description": "Venda importada",
        "amount_cents": 10000,
        "category_name": "Vendas",
        "paid": True,
    }
    defaults.update(overrides)
    return ImportRow(**defaults)


async def test_imports_rows_creating_categories_on_demand() -> None:
    categories = FakeFinancialCategoryRepository()
    transactions = FakeFinancialTransactionRepository()

    result = await ImportTransactionsUseCase(categories, transactions).execute(
        rows=[
            _row(),
            _row(description="Outra venda", amount_cents=5000),
            _row(description="Aluguel", amount_cents=-300000, category_name="Aluguel"),
        ],
        created_by="user-1",
    )

    assert result.imported == 3
    # "Vendas" (income) e "Aluguel" (expense)
    assert result.categories_created == 2
    created = await transactions.list_all()
    assert len(created) == 3
    expense = next(t for t in created if t.type == FinancialCategoryType.EXPENSE)
    assert expense.amount_cents == 300000  # valor absoluto
    assert expense.status == TransactionStatus.PAID


async def test_reuses_existing_category_case_insensitive() -> None:
    categories = FakeFinancialCategoryRepository()
    await categories.create(name="Vendas", type=FinancialCategoryType.INCOME)
    transactions = FakeFinancialTransactionRepository()

    result = await ImportTransactionsUseCase(categories, transactions).execute(
        rows=[_row(category_name="vendas"), _row(category_name="VENDAS")],
        created_by="user-1",
    )

    assert result.categories_created == 0
    assert result.imported == 2


async def test_rows_without_category_fall_into_default() -> None:
    categories = FakeFinancialCategoryRepository()
    transactions = FakeFinancialTransactionRepository()

    await ImportTransactionsUseCase(categories, transactions).execute(
        rows=[_row(category_name=None), _row(category_name="  ")],
        created_by="user-1",
    )

    names = [c.name for c in await categories.list_all(only_active=False)]
    assert names == ["Importados"]


async def test_unpaid_rows_become_pending_with_due_date() -> None:
    categories = FakeFinancialCategoryRepository()
    transactions = FakeFinancialTransactionRepository()
    due = datetime(2026, 7, 10, tzinfo=UTC)

    await ImportTransactionsUseCase(categories, transactions).execute(
        rows=[_row(paid=False, date=due, amount_cents=-5000)],
        created_by="user-1",
    )

    [transaction] = await transactions.list_all()
    assert transaction.status == TransactionStatus.PENDING
    assert transaction.due_date == due
    assert transaction.paid_at is None
