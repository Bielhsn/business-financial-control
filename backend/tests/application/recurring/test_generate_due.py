from datetime import UTC, datetime

import pytest

from app.application.recurring.generate_due import GenerateDueRecurringUseCase
from app.domain.financial.entities import FinancialCategoryType, TransactionStatus
from app.domain.recurring.entities import RecurrenceFrequency, RecurringTransaction
from tests.fakes import (
    FakeFinancialTransactionRepository,
    FakeRecurringTransactionRepository,
)

pytestmark = pytest.mark.anyio


def _recurring(
    recurring_id: str,
    *,
    next_run: datetime,
    frequency: RecurrenceFrequency = RecurrenceFrequency.MONTHLY,
    active: bool = True,
) -> RecurringTransaction:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    return RecurringTransaction(
        id=recurring_id,
        company_id="company-1",
        category_id="cat-rent",
        type=FinancialCategoryType.EXPENSE,
        amount_cents=250000,
        description="Aluguel",
        frequency=frequency,
        anchor_day=next_run.day,
        next_run_date=next_run,
        active=active,
        notes="Contrato",
        client_id=None,
        created_by="user-1",
        created_at=now,
        updated_at=now,
    )


async def test_generates_pending_transaction_and_advances_next_date() -> None:
    recurring = FakeRecurringTransactionRepository(
        [_recurring("r1", next_run=datetime(2026, 7, 5, tzinfo=UTC))]
    )
    transactions = FakeFinancialTransactionRepository()

    result = await GenerateDueRecurringUseCase(recurring, transactions).execute(
        as_of=datetime(2026, 7, 20, tzinfo=UTC), created_by="user-1"
    )

    assert result.created == 1
    created = (await transactions.list_all())[0]
    assert created.status == TransactionStatus.PENDING
    assert created.due_date == datetime(2026, 7, 5, tzinfo=UTC)
    assert created.amount_cents == 250000
    assert created.external_ref == "recurring:r1:2026-07-05"

    item = await recurring.get_by_id("r1")
    assert item is not None
    assert item.next_run_date == datetime(2026, 8, 5, tzinfo=UTC)
    assert item.last_run_at == datetime(2026, 7, 5, tzinfo=UTC)


async def test_catches_up_multiple_missed_periods() -> None:
    recurring = FakeRecurringTransactionRepository(
        [_recurring("r1", next_run=datetime(2026, 5, 10, tzinfo=UTC))]
    )
    transactions = FakeFinancialTransactionRepository()

    # De maio a julho, com next em 10: gera 10/05, 10/06, 10/07.
    result = await GenerateDueRecurringUseCase(recurring, transactions).execute(
        as_of=datetime(2026, 7, 20, tzinfo=UTC), created_by="user-1"
    )

    assert result.created == 3
    item = await recurring.get_by_id("r1")
    assert item is not None
    assert item.next_run_date == datetime(2026, 8, 10, tzinfo=UTC)


async def test_is_idempotent_across_runs() -> None:
    recurring = FakeRecurringTransactionRepository(
        [_recurring("r1", next_run=datetime(2026, 7, 5, tzinfo=UTC))]
    )
    transactions = FakeFinancialTransactionRepository()
    use_case = GenerateDueRecurringUseCase(recurring, transactions)

    first = await use_case.execute(as_of=datetime(2026, 7, 6, tzinfo=UTC), created_by="u")
    second = await use_case.execute(as_of=datetime(2026, 7, 6, tzinfo=UTC), created_by="u")

    assert first.created == 1
    assert second.created == 0
    assert len(await transactions.list_all()) == 1


async def test_skips_inactive_and_future() -> None:
    recurring = FakeRecurringTransactionRepository(
        [
            _recurring("r1", next_run=datetime(2026, 7, 5, tzinfo=UTC), active=False),
            _recurring("r2", next_run=datetime(2026, 9, 1, tzinfo=UTC)),
        ]
    )
    transactions = FakeFinancialTransactionRepository()

    result = await GenerateDueRecurringUseCase(recurring, transactions).execute(
        as_of=datetime(2026, 7, 20, tzinfo=UTC), created_by="u"
    )

    assert result.created == 0
    assert await transactions.list_all() == []
