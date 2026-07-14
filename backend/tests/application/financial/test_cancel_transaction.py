import pytest

from app.application.financial.cancel_transaction import CancelTransactionUseCase
from app.core.exceptions import ConflictError, NotFoundError
from app.domain.financial.entities import FinancialCategoryType, TransactionStatus
from tests.fakes import FakeFinancialTransactionRepository

pytestmark = pytest.mark.anyio


async def test_cancels_a_pending_transaction() -> None:
    repository = FakeFinancialTransactionRepository()
    transaction = await repository.create(
        category_id="category-1",
        type=FinancialCategoryType.EXPENSE,
        amount_cents=1000,
        description="X",
        status=TransactionStatus.PENDING,
        due_date=None,
        paid_at=None,
        notes=None,
        created_by="user-1",
    )

    updated = await CancelTransactionUseCase(repository).execute(transaction_id=transaction.id)

    assert updated.status == TransactionStatus.CANCELLED


async def test_raises_conflict_when_cancelling_a_paid_transaction() -> None:
    repository = FakeFinancialTransactionRepository()
    transaction = await repository.create(
        category_id="category-1",
        type=FinancialCategoryType.EXPENSE,
        amount_cents=1000,
        description="X",
        status=TransactionStatus.PAID,
        due_date=None,
        paid_at=None,
        notes=None,
        created_by="user-1",
    )

    with pytest.raises(ConflictError):
        await CancelTransactionUseCase(repository).execute(transaction_id=transaction.id)


async def test_raises_not_found_for_unknown_transaction() -> None:
    with pytest.raises(NotFoundError):
        await CancelTransactionUseCase(FakeFinancialTransactionRepository()).execute(
            transaction_id="does-not-exist"
        )
