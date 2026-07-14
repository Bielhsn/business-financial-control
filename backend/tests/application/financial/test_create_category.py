import pytest

from app.application.financial.create_category import CreateFinancialCategoryUseCase
from app.core.exceptions import ConflictError
from app.domain.financial.entities import FinancialCategoryType
from tests.fakes import FakeFinancialCategoryRepository

pytestmark = pytest.mark.anyio


async def test_creates_a_category_with_a_normalized_name() -> None:
    use_case = CreateFinancialCategoryUseCase(FakeFinancialCategoryRepository())

    category = await use_case.execute(name="  Vendas  ", type=FinancialCategoryType.INCOME)

    assert category.name == "Vendas"
    assert category.type == FinancialCategoryType.INCOME
    assert category.is_active is True


async def test_raises_conflict_for_duplicate_name_and_type() -> None:
    repository = FakeFinancialCategoryRepository()
    use_case = CreateFinancialCategoryUseCase(repository)
    await use_case.execute(name="Vendas", type=FinancialCategoryType.INCOME)

    with pytest.raises(ConflictError):
        await use_case.execute(name="Vendas", type=FinancialCategoryType.INCOME)


async def test_allows_same_name_with_different_type() -> None:
    repository = FakeFinancialCategoryRepository()
    use_case = CreateFinancialCategoryUseCase(repository)
    await use_case.execute(name="Aluguel", type=FinancialCategoryType.EXPENSE)

    category = await use_case.execute(name="Aluguel", type=FinancialCategoryType.INCOME)

    assert category.type == FinancialCategoryType.INCOME
