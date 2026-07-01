from datetime import UTC, datetime

import pytest

from app.application.financial.mark_transaction_paid import MarkTransactionPaidUseCase
from app.core.exceptions import ConflictError, NotFoundError
from app.domain.financial.entities import FinancialCategoryType, TransactionStatus
from tests.fakes import FakeFinancialTransactionRepository

pytestmark = pytest.mark.anyio


async def _create_pending_transaction(repository: FakeFinancialTransactionRepository) -> str:
    transaction = await repository.create(
        category_id="category-1",
        type=FinancialCategoryType.INCOME,
        amount_cents=1000,
        description="X",
        status=TransactionStatus.PENDING,
        due_date=None,
        paid_at=None,
        notes=None,
        created_by="user-1",
    )
    return transaction.id


async def test_marks_a_pending_transaction_as_paid() -> None:
    repository = FakeFinancialTransactionRepository()
    transaction_id = await _create_pending_transaction(repository)

    updated = await MarkTransactionPaidUseCase(repository).execute(transaction_id=transaction_id)

    assert updated.status == TransactionStatus.PAID
    assert updated.paid_at is not None


async def test_uses_the_given_paid_at() -> None:
    repository = FakeFinancialTransactionRepository()
    transaction_id = await _create_pending_transaction(repository)
    paid_at = datetime(2026, 1, 1, tzinfo=UTC)

    updated = await MarkTransactionPaidUseCase(repository).execute(
        transaction_id=transaction_id, paid_at=paid_at
    )

    assert updated.paid_at == paid_at


async def test_is_idempotent_for_an_already_paid_transaction() -> None:
    repository = FakeFinancialTransactionRepository()
    transaction_id = await _create_pending_transaction(repository)
    first = await MarkTransactionPaidUseCase(repository).execute(transaction_id=transaction_id)

    second = await MarkTransactionPaidUseCase(repository).execute(transaction_id=transaction_id)

    assert second.paid_at == first.paid_at


async def test_raises_conflict_for_a_cancelled_transaction() -> None:
    repository = FakeFinancialTransactionRepository()
    transaction_id = await _create_pending_transaction(repository)
    await repository.update(transaction_id, status=TransactionStatus.CANCELLED)

    with pytest.raises(ConflictError):
        await MarkTransactionPaidUseCase(repository).execute(transaction_id=transaction_id)


async def test_raises_not_found_for_unknown_transaction() -> None:
    with pytest.raises(NotFoundError):
        await MarkTransactionPaidUseCase(FakeFinancialTransactionRepository()).execute(
            transaction_id="does-not-exist"
        )
