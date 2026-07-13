from datetime import UTC, datetime, timedelta

import pytest

from app.application.notifications.get_notifications import (
    GetNotificationsUseCase,
    NotificationKind,
)
from app.domain.financial.entities import FinancialCategoryType, TransactionStatus
from tests.fakes import FakeFinancialTransactionRepository

pytestmark = pytest.mark.anyio


async def _pending(repository: FakeFinancialTransactionRepository, due_date, description="Conta"):
    await repository.create(
        category_id="c1",
        type=FinancialCategoryType.EXPENSE,
        amount_cents=5000,
        description=description,
        status=TransactionStatus.PENDING,
        due_date=due_date,
        paid_at=None,
        notes=None,
        created_by="user-1",
    )


async def test_classifies_overdue_and_due_soon_ordering_overdue_first() -> None:
    repository = FakeFinancialTransactionRepository()
    now = datetime.now(UTC)
    await _pending(repository, now + timedelta(days=2), "Vence em breve")
    await _pending(repository, now - timedelta(days=3), "Vencida")

    notifications = await GetNotificationsUseCase(repository).execute()

    assert [n.kind for n in notifications] == [
        NotificationKind.OVERDUE,
        NotificationKind.DUE_SOON,
    ]
    assert notifications[0].description == "Vencida"


async def test_ignores_far_future_and_paid_transactions() -> None:
    repository = FakeFinancialTransactionRepository()
    now = datetime.now(UTC)
    await _pending(repository, now + timedelta(days=30), "Longe demais")
    await repository.create(
        category_id="c1",
        type=FinancialCategoryType.INCOME,
        amount_cents=1000,
        description="Já paga",
        status=TransactionStatus.PAID,
        due_date=None,
        paid_at=now,
        notes=None,
        created_by="user-1",
    )

    notifications = await GetNotificationsUseCase(repository).execute()

    assert notifications == []
