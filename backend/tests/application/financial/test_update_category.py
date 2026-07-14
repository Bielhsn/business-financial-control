import pytest

from app.application.financial.create_category import CreateFinancialCategoryUseCase
from app.application.financial.update_category import UpdateFinancialCategoryUseCase
from app.core.exceptions import NotFoundError
from app.domain.financial.entities import FinancialCategoryType
from tests.fakes import FakeFinancialCategoryRepository

pytestmark = pytest.mark.anyio


async def test_updates_only_the_provided_fields() -> None:
    repository = FakeFinancialCategoryRepository()
    category = await CreateFinancialCategoryUseCase(repository).execute(
        name="Vendas", type=FinancialCategoryType.INCOME
    )

    updated = await UpdateFinancialCategoryUseCase(repository).execute(
        category_id=category.id, name="Vendas de serviços"
    )

    assert updated.name == "Vendas de serviços"
    assert updated.type == FinancialCategoryType.INCOME


async def test_can_deactivate_a_category() -> None:
    repository = FakeFinancialCategoryRepository()
    category = await CreateFinancialCategoryUseCase(repository).execute(
        name="Vendas", type=FinancialCategoryType.INCOME
    )

    updated = await UpdateFinancialCategoryUseCase(repository).execute(
        category_id=category.id, is_active=False
    )

    assert updated.is_active is False


async def test_raises_not_found_for_unknown_category() -> None:
    repository = FakeFinancialCategoryRepository()

    with pytest.raises(NotFoundError):
        await UpdateFinancialCategoryUseCase(repository).execute(
            category_id="does-not-exist", name="Novo nome"
        )


async def test_returns_category_unchanged_when_no_fields_are_provided() -> None:
    repository = FakeFinancialCategoryRepository()
    category = await CreateFinancialCategoryUseCase(repository).execute(
        name="Vendas", type=FinancialCategoryType.INCOME
    )

    result = await UpdateFinancialCategoryUseCase(repository).execute(category_id=category.id)

    assert result.name == "Vendas"


async def test_raises_not_found_when_no_fields_are_provided_for_unknown_category() -> None:
    repository = FakeFinancialCategoryRepository()

    with pytest.raises(NotFoundError):
        await UpdateFinancialCategoryUseCase(repository).execute(category_id="does-not-exist")
