from datetime import UTC, datetime, timedelta

import pytest

from app.application.financial.create_category import CreateFinancialCategoryUseCase
from app.application.financial.create_transaction import CreateFinancialTransactionUseCase
from app.core.exceptions import NotFoundError, ValidationError
from app.domain.financial.entities import FinancialCategoryType, TransactionStatus
from tests.fakes import (
    FakeClientRepository,
    FakeFinancialCategoryRepository,
    FakeFinancialTransactionRepository,
)

pytestmark = pytest.mark.anyio


async def _create_category(
    category_repository: FakeFinancialCategoryRepository,
    type: FinancialCategoryType = FinancialCategoryType.INCOME,
) -> str:
    category = await CreateFinancialCategoryUseCase(category_repository).execute(
        name="Vendas", type=type
    )
    return category.id


def _use_case(
    category_repository: FakeFinancialCategoryRepository,
) -> CreateFinancialTransactionUseCase:
    return CreateFinancialTransactionUseCase(
        category_repository, FakeFinancialTransactionRepository(), FakeClientRepository()
    )


async def test_creates_a_pending_transaction_without_paid_at() -> None:
    category_repository = FakeFinancialCategoryRepository()
    category_id = await _create_category(category_repository)
    use_case = _use_case(category_repository)

    transaction = await use_case.execute(
        category_id=category_id,
        type=FinancialCategoryType.INCOME,
        amount_cents=15000,
        description="Corte de cabelo",
        due_date=datetime.now(UTC) + timedelta(days=5),
        paid_at=None,
        notes=None,
        client_id=None,
        created_by="user-1",
    )

    assert transaction.status == TransactionStatus.PENDING
    assert transaction.paid_at is None


async def test_creates_a_paid_transaction_when_paid_at_is_given() -> None:
    category_repository = FakeFinancialCategoryRepository()
    category_id = await _create_category(category_repository)
    use_case = _use_case(category_repository)

    transaction = await use_case.execute(
        category_id=category_id,
        type=FinancialCategoryType.INCOME,
        amount_cents=15000,
        description="Corte de cabelo",
        due_date=None,
        paid_at=datetime.now(UTC),
        notes="Pago em dinheiro",
        client_id=None,
        created_by="user-1",
    )

    assert transaction.status == TransactionStatus.PAID
    assert transaction.paid_at is not None


async def test_links_the_transaction_to_an_existing_client() -> None:
    category_repository = FakeFinancialCategoryRepository()
    category_id = await _create_category(category_repository)
    client_repository = FakeClientRepository()
    client = await client_repository.create(
        name="Ana", email=None, phone=None, notes=None, custom_fields={}
    )
    use_case = CreateFinancialTransactionUseCase(
        category_repository, FakeFinancialTransactionRepository(), client_repository
    )

    transaction = await use_case.execute(
        category_id=category_id,
        type=FinancialCategoryType.INCOME,
        amount_cents=15000,
        description="Corte de cabelo",
        due_date=None,
        paid_at=datetime.now(UTC),
        notes=None,
        client_id=client.id,
        created_by="user-1",
    )

    assert transaction.client_id == client.id


async def test_raises_not_found_for_unknown_client() -> None:
    category_repository = FakeFinancialCategoryRepository()
    category_id = await _create_category(category_repository)
    use_case = _use_case(category_repository)

    with pytest.raises(NotFoundError):
        await use_case.execute(
            category_id=category_id,
            type=FinancialCategoryType.INCOME,
            amount_cents=1000,
            description="X",
            due_date=None,
            paid_at=None,
            notes=None,
            client_id="does-not-exist",
            created_by="user-1",
        )


async def test_raises_not_found_for_unknown_category() -> None:
    use_case = _use_case(FakeFinancialCategoryRepository())

    with pytest.raises(NotFoundError):
        await use_case.execute(
            category_id="does-not-exist",
            type=FinancialCategoryType.INCOME,
            amount_cents=1000,
            description="X",
            due_date=None,
            paid_at=None,
            notes=None,
            client_id=None,
            created_by="user-1",
        )


async def test_raises_validation_error_when_type_does_not_match_category() -> None:
    category_repository = FakeFinancialCategoryRepository()
    category_id = await _create_category(category_repository, type=FinancialCategoryType.EXPENSE)
    use_case = _use_case(category_repository)

    with pytest.raises(ValidationError):
        await use_case.execute(
            category_id=category_id,
            type=FinancialCategoryType.INCOME,
            amount_cents=1000,
            description="X",
            due_date=None,
            paid_at=None,
            notes=None,
            client_id=None,
            created_by="user-1",
        )


async def test_raises_validation_error_for_non_positive_amount() -> None:
    category_repository = FakeFinancialCategoryRepository()
    category_id = await _create_category(category_repository)
    use_case = _use_case(category_repository)

    with pytest.raises(ValidationError):
        await use_case.execute(
            category_id=category_id,
            type=FinancialCategoryType.INCOME,
            amount_cents=0,
            description="X",
            due_date=None,
            paid_at=None,
            notes=None,
            client_id=None,
            created_by="user-1",
        )


async def test_raises_not_found_for_inactive_category() -> None:
    category_repository = FakeFinancialCategoryRepository()
    category_id = await _create_category(category_repository)
    category = await category_repository.get_by_id(category_id)
    assert category is not None
    category.is_active = False
    use_case = _use_case(category_repository)

    with pytest.raises(NotFoundError):
        await use_case.execute(
            category_id=category_id,
            type=FinancialCategoryType.INCOME,
            amount_cents=1000,
            description="X",
            due_date=None,
            paid_at=None,
            notes=None,
            client_id=None,
            created_by="user-1",
        )
