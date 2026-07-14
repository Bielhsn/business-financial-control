import pytest

from app.application.catalog.adjust_stock import AdjustStockUseCase
from app.application.catalog.create_item import CreateCatalogItemUseCase
from app.core.exceptions import NotFoundError, ValidationError
from app.domain.catalog.entities import CatalogItemKind
from tests.fakes import FakeCatalogItemRepository, FakeStockMovementRepository

pytestmark = pytest.mark.anyio


async def _create_product(
    repository: FakeCatalogItemRepository, *, stock_quantity: int = 10
) -> str:
    item = await CreateCatalogItemUseCase(repository).execute(
        name="Shampoo",
        description=None,
        price_cents=2500,
        kind=CatalogItemKind.PRODUCT,
        tracks_inventory=True,
        stock_quantity=stock_quantity,
    )
    return item.id


async def test_increases_stock_and_logs_a_movement() -> None:
    item_repository = FakeCatalogItemRepository()
    item_id = await _create_product(item_repository)
    movement_repository = FakeStockMovementRepository()

    item = await AdjustStockUseCase(item_repository, movement_repository).execute(
        item_id=item_id, delta=5, reason="Compra de estoque", created_by="user-1"
    )

    assert item.stock_quantity == 15
    movements = await movement_repository.list_for_item(item_id)
    assert len(movements) == 1
    assert movements[0].delta == 5


async def test_decreases_stock() -> None:
    item_repository = FakeCatalogItemRepository()
    item_id = await _create_product(item_repository)
    movement_repository = FakeStockMovementRepository()

    item = await AdjustStockUseCase(item_repository, movement_repository).execute(
        item_id=item_id, delta=-3, reason="Venda", created_by="user-1"
    )

    assert item.stock_quantity == 7


async def test_rejects_adjustment_that_would_go_negative() -> None:
    item_repository = FakeCatalogItemRepository()
    item_id = await _create_product(item_repository, stock_quantity=2)
    movement_repository = FakeStockMovementRepository()

    with pytest.raises(ValidationError):
        await AdjustStockUseCase(item_repository, movement_repository).execute(
            item_id=item_id, delta=-3, reason="Venda", created_by="user-1"
        )


async def test_rejects_zero_delta() -> None:
    item_repository = FakeCatalogItemRepository()
    item_id = await _create_product(item_repository)
    movement_repository = FakeStockMovementRepository()

    with pytest.raises(ValidationError):
        await AdjustStockUseCase(item_repository, movement_repository).execute(
            item_id=item_id, delta=0, reason="Nada", created_by="user-1"
        )


async def test_rejects_adjustment_for_item_without_inventory_tracking() -> None:
    item_repository = FakeCatalogItemRepository()
    item = await CreateCatalogItemUseCase(item_repository).execute(
        name="Corte de cabelo",
        description=None,
        price_cents=3000,
        kind=CatalogItemKind.SERVICE,
        tracks_inventory=False,
        stock_quantity=None,
    )
    movement_repository = FakeStockMovementRepository()

    with pytest.raises(ValidationError):
        await AdjustStockUseCase(item_repository, movement_repository).execute(
            item_id=item.id, delta=5, reason="X", created_by="user-1"
        )


async def test_raises_not_found_for_unknown_item() -> None:
    with pytest.raises(NotFoundError):
        await AdjustStockUseCase(
            FakeCatalogItemRepository(), FakeStockMovementRepository()
        ).execute(item_id="does-not-exist", delta=1, reason="X", created_by="user-1")
