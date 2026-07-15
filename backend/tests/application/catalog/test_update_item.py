import pytest

from app.application.catalog.create_item import CreateCatalogItemUseCase
from app.application.catalog.update_item import UpdateCatalogItemUseCase
from app.core.exceptions import NotFoundError, ValidationError
from app.domain.catalog.entities import CatalogItemKind, ProductVariant
from tests.fakes import FakeCatalogItemRepository

pytestmark = pytest.mark.anyio


async def _create_item(repository: FakeCatalogItemRepository) -> str:
    item = await CreateCatalogItemUseCase(repository).execute(
        name="Shampoo",
        description=None,
        price_cents=2500,
        kind=CatalogItemKind.PRODUCT,
        tracks_inventory=True,
        stock_quantity=10,
    )
    return item.id


async def test_updates_only_the_provided_fields() -> None:
    repository = FakeCatalogItemRepository()
    item_id = await _create_item(repository)

    updated = await UpdateCatalogItemUseCase(repository).execute(
        item_id=item_id, name="Shampoo 500ml"
    )

    assert updated.name == "Shampoo 500ml"
    assert updated.price_cents == 2500


async def test_rejects_non_positive_price() -> None:
    repository = FakeCatalogItemRepository()
    item_id = await _create_item(repository)

    with pytest.raises(ValidationError):
        await UpdateCatalogItemUseCase(repository).execute(item_id=item_id, price_cents=0)


async def test_raises_not_found_for_unknown_item() -> None:
    with pytest.raises(NotFoundError):
        await UpdateCatalogItemUseCase(FakeCatalogItemRepository()).execute(
            item_id="does-not-exist", name="X"
        )


async def test_returns_item_unchanged_when_no_fields_are_provided() -> None:
    repository = FakeCatalogItemRepository()
    item_id = await _create_item(repository)

    result = await UpdateCatalogItemUseCase(repository).execute(item_id=item_id)

    assert result.name == "Shampoo"


async def test_raises_not_found_when_no_fields_are_provided_for_unknown_item() -> None:
    with pytest.raises(NotFoundError):
        await UpdateCatalogItemUseCase(FakeCatalogItemRepository()).execute(
            item_id="does-not-exist"
        )


async def test_rejects_promo_price_above_current_price() -> None:
    repository = FakeCatalogItemRepository()
    item_id = await _create_item(repository)

    with pytest.raises(ValidationError, match="promocional"):
        await UpdateCatalogItemUseCase(repository).execute(item_id=item_id, promo_price_cents=9999)


async def test_accepts_promo_price_below_new_price_in_same_update() -> None:
    repository = FakeCatalogItemRepository()
    item_id = await _create_item(repository)

    updated = await UpdateCatalogItemUseCase(repository).execute(
        item_id=item_id, price_cents=10000, promo_price_cents=8000
    )

    assert updated.promo_price_cents == 8000


async def test_rejects_sku_already_used_by_another_item() -> None:
    repository = FakeCatalogItemRepository()
    await CreateCatalogItemUseCase(repository).execute(
        name="Condicionador",
        description=None,
        price_cents=3000,
        kind=CatalogItemKind.PRODUCT,
        tracks_inventory=False,
        stock_quantity=None,
        sku="SH-01",
    )
    item_id = await _create_item(repository)

    with pytest.raises(ValidationError, match="SKU"):
        await UpdateCatalogItemUseCase(repository).execute(item_id=item_id, sku="SH-01")


async def test_replaces_variants_and_allows_clearing_lists() -> None:
    repository = FakeCatalogItemRepository()
    item_id = await _create_item(repository)

    updated = await UpdateCatalogItemUseCase(repository).execute(
        item_id=item_id,
        tags=["promo"],
        variants=[ProductVariant(name="500ml", stock_quantity=3)],
    )
    assert updated.tags == ["promo"]
    assert len(updated.variants) == 1

    cleared = await UpdateCatalogItemUseCase(repository).execute(
        item_id=item_id, tags=[], variants=[]
    )
    assert cleared.tags == []
    assert cleared.variants == []


async def test_rejects_invalid_variants_on_update() -> None:
    repository = FakeCatalogItemRepository()
    item_id = await _create_item(repository)

    with pytest.raises(ValidationError, match="duplicada"):
        await UpdateCatalogItemUseCase(repository).execute(
            item_id=item_id,
            variants=[ProductVariant(name="M"), ProductVariant(name="m")],
        )
