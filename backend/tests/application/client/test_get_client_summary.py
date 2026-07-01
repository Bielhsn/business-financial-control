from datetime import UTC, datetime, timedelta

import pytest

from app.application.client.get_client_summary import GetClientSummaryUseCase
from app.core.exceptions import NotFoundError
from app.domain.financial.entities import FinancialCategoryType, TransactionStatus
from tests.fakes import FakeClientRepository, FakeFinancialTransactionRepository

pytestmark = pytest.mark.anyio


async def test_summarizes_paid_purchases_for_a_client() -> None:
    client_repository = FakeClientRepository()
    client = await client_repository.create(
        name="Ana", email=None, phone=None, notes=None, custom_fields={}
    )
    transaction_repository = FakeFinancialTransactionRepository()
    now = datetime.now(UTC)
    await transaction_repository.create(
        category_id="c1",
        type=FinancialCategoryType.INCOME,
        amount_cents=15000,
        description="Corte",
        status=TransactionStatus.PAID,
        due_date=None,
        paid_at=now - timedelta(days=10),
        notes=None,
        client_id=client.id,
        created_by="user-1",
    )
    await transaction_repository.create(
        category_id="c1",
        type=FinancialCategoryType.INCOME,
        amount_cents=5000,
        description="Barba",
        status=TransactionStatus.PAID,
        due_date=None,
        paid_at=now,
        notes=None,
        client_id=client.id,
        created_by="user-1",
    )
    # pendente: não deve entrar no resumo
    await transaction_repository.create(
        category_id="c1",
        type=FinancialCategoryType.INCOME,
        amount_cents=99999,
        description="Ainda não pago",
        status=TransactionStatus.PENDING,
        due_date=None,
        paid_at=None,
        notes=None,
        client_id=client.id,
        created_by="user-1",
    )

    summary = await GetClientSummaryUseCase(client_repository, transaction_repository).execute(
        client_id=client.id
    )

    assert summary.total_spent_cents == 20000
    assert summary.purchase_count == 2
    assert summary.last_purchase_at == now


async def test_raises_not_found_for_unknown_client() -> None:
    with pytest.raises(NotFoundError):
        await GetClientSummaryUseCase(
            FakeClientRepository(), FakeFinancialTransactionRepository()
        ).execute(client_id="does-not-exist")
