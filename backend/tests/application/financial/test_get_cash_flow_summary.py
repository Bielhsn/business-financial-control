from datetime import UTC, datetime, timedelta

import pytest

from app.application.financial.get_cash_flow_summary import GetCashFlowSummaryUseCase
from app.domain.financial.entities import FinancialCategoryType, TransactionStatus
from tests.fakes import FakeFinancialTransactionRepository

pytestmark = pytest.mark.anyio


async def test_sums_paid_income_and_expense_within_the_period() -> None:
    repository = FakeFinancialTransactionRepository()
    now = datetime.now(UTC)

    await repository.create(
        category_id="c1",
        type=FinancialCategoryType.INCOME,
        amount_cents=10000,
        description="Venda",
        status=TransactionStatus.PAID,
        due_date=None,
        paid_at=now,
        notes=None,
        created_by="user-1",
    )
    await repository.create(
        category_id="c2",
        type=FinancialCategoryType.EXPENSE,
        amount_cents=4000,
        description="Aluguel",
        status=TransactionStatus.PAID,
        due_date=None,
        paid_at=now,
        notes=None,
        created_by="user-1",
    )
    # pendente: não deve entrar na soma do fluxo de caixa realizado
    await repository.create(
        category_id="c1",
        type=FinancialCategoryType.INCOME,
        amount_cents=99999,
        description="Ainda não recebido",
        status=TransactionStatus.PENDING,
        due_date=now + timedelta(days=10),
        paid_at=None,
        notes=None,
        created_by="user-1",
    )

    summary = await GetCashFlowSummaryUseCase(repository).execute(
        start=now - timedelta(days=1), end=now + timedelta(days=1)
    )

    assert summary.income_cents == 10000
    assert summary.expense_cents == 4000
    assert summary.balance_cents == 6000


async def test_ignores_transactions_paid_outside_the_period() -> None:
    repository = FakeFinancialTransactionRepository()
    now = datetime.now(UTC)
    await repository.create(
        category_id="c1",
        type=FinancialCategoryType.INCOME,
        amount_cents=10000,
        description="Venda antiga",
        status=TransactionStatus.PAID,
        due_date=None,
        paid_at=now - timedelta(days=60),
        notes=None,
        created_by="user-1",
    )

    summary = await GetCashFlowSummaryUseCase(repository).execute(
        start=now - timedelta(days=1), end=now + timedelta(days=1)
    )

    assert summary.income_cents == 0
    assert summary.balance_cents == 0
