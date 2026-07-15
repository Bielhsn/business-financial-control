import pytest

from app.application.catalog.create_item import CreateCatalogItemUseCase
from app.core.exceptions import ValidationError
from app.domain.catalog.entities import CatalogItemKind, ProductVariant
from tests.fakes import FakeCatalogItemRepository

pytestmark = pytest.mark.anyio


async def test_creates_a_service_without_stock_tracking() -> None:
    item = await CreateCatalogItemUseCase(FakeCatalogItemRepository()).execute(
        name="Corte de cabelo",
        description=None,
        price_cents=3000,
        kind=CatalogItemKind.SERVICE,
        tracks_inventory=False,
        stock_quantity=None,
    )

    assert item.kind == CatalogItemKind.SERVICE
    assert item.stock_quantity is None


async def test_rejects_a_service_that_tracks_inventory() -> None:
    with pytest.raises(ValidationError):
        await CreateCatalogItemUseCase(FakeCatalogItemRepository()).execute(
            name="Corte de cabelo",
            description=None,
            price_cents=3000,
            kind=CatalogItemKind.SERVICE,
            tracks_inventory=True,
            stock_quantity=None,
        )


async def test_creates_a_product_with_stock_tracking_defaulting_to_zero() -> None:
    item = await CreateCatalogItemUseCase(FakeCatalogItemRepository()).execute(
        name="Shampoo",
        description="500ml",
        price_cents=2500,
        kind=CatalogItemKind.PRODUCT,
        tracks_inventory=True,
        stock_quantity=None,
    )

    assert item.stock_quantity == 0


async def test_rejects_negative_initial_stock() -> None:
    with pytest.raises(ValidationError):
        await CreateCatalogItemUseCase(FakeCatalogItemRepository()).execute(
            name="Shampoo",
            description=None,
            price_cents=2500,
            kind=CatalogItemKind.PRODUCT,
            tracks_inventory=True,
            stock_quantity=-1,
        )


async def test_rejects_non_positive_price() -> None:
    with pytest.raises(ValidationError):
        await CreateCatalogItemUseCase(FakeCatalogItemRepository()).execute(
            name="Shampoo",
            description=None,
            price_cents=0,
            kind=CatalogItemKind.PRODUCT,
            tracks_inventory=False,
            stock_quantity=None,
        )


async def test_product_without_inventory_tracking_has_no_stock_quantity() -> None:
    item = await CreateCatalogItemUseCase(FakeCatalogItemRepository()).execute(
        name="Bundle promocional",
        description=None,
        price_cents=9900,
        kind=CatalogItemKind.PRODUCT,
        tracks_inventory=False,
        stock_quantity=None,
    )

    assert item.stock_quantity is None


async def test_creates_a_full_professional_product() -> None:
    item = await CreateCatalogItemUseCase(FakeCatalogItemRepository()).execute(
        name="Camiseta básica",
        description="Camiseta 100% algodão, corte unissex.",
        price_cents=7990,
        kind=CatalogItemKind.PRODUCT,
        tracks_inventory=True,
        stock_quantity=10,
        sku="CAM-001",
        barcode="7891234567890",
        brand="Aurum Wear",
        supplier="Malharia Sul",
        category="Vestuário",
        subcategory="Camisetas",
        short_description="Camiseta básica de algodão.",
        tags=["algodão", "básico"],
        cost_price_cents=3200,
        promo_price_cents=5990,
        min_stock=5,
        max_stock=100,
        stock_location="Prateleira A3",
        images=["data:image/png;base64,AAAA"],
        variants=[
            ProductVariant(name="Azul / M", sku="CAM-001-AM", stock_quantity=4),
            ProductVariant(name="Azul / G", sku="CAM-001-AG", stock_quantity=6),
        ],
    )

    assert item.sku == "CAM-001"
    assert item.category == "Vestuário"
    assert item.tags == ["algodão", "básico"]
    assert len(item.variants) == 2
    assert item.variants[0].name == "Azul / M"


async def test_rejects_duplicate_sku() -> None:
    repository = FakeCatalogItemRepository()
    use_case = CreateCatalogItemUseCase(repository)
    await use_case.execute(
        name="Camiseta",
        description=None,
        price_cents=7990,
        kind=CatalogItemKind.PRODUCT,
        tracks_inventory=False,
        stock_quantity=None,
        sku="CAM-001",
    )

    with pytest.raises(ValidationError, match="SKU"):
        await use_case.execute(
            name="Outra camiseta",
            description=None,
            price_cents=8990,
            kind=CatalogItemKind.PRODUCT,
            tracks_inventory=False,
            stock_quantity=None,
            sku="CAM-001",
        )


async def test_rejects_promo_price_not_below_price() -> None:
    with pytest.raises(ValidationError, match="promocional"):
        await CreateCatalogItemUseCase(FakeCatalogItemRepository()).execute(
            name="Camiseta",
            description=None,
            price_cents=7990,
            kind=CatalogItemKind.PRODUCT,
            tracks_inventory=False,
            stock_quantity=None,
            promo_price_cents=7990,
        )


async def test_rejects_min_stock_above_max_stock() -> None:
    with pytest.raises(ValidationError, match="mínimo"):
        await CreateCatalogItemUseCase(FakeCatalogItemRepository()).execute(
            name="Camiseta",
            description=None,
            price_cents=7990,
            kind=CatalogItemKind.PRODUCT,
            tracks_inventory=True,
            stock_quantity=0,
            min_stock=50,
            max_stock=10,
        )


async def test_rejects_duplicate_variant_names_and_skus() -> None:
    with pytest.raises(ValidationError, match="duplicada"):
        await CreateCatalogItemUseCase(FakeCatalogItemRepository()).execute(
            name="Camiseta",
            description=None,
            price_cents=7990,
            kind=CatalogItemKind.PRODUCT,
            tracks_inventory=False,
            stock_quantity=None,
            variants=[
                ProductVariant(name="Azul / M"),
                ProductVariant(name="azul / m"),
            ],
        )

    with pytest.raises(ValidationError, match="SKU de variação"):
        await CreateCatalogItemUseCase(FakeCatalogItemRepository()).execute(
            name="Camiseta",
            description=None,
            price_cents=7990,
            kind=CatalogItemKind.PRODUCT,
            tracks_inventory=False,
            stock_quantity=None,
            variants=[
                ProductVariant(name="Azul / M", sku="X-1"),
                ProductVariant(name="Azul / G", sku="X-1"),
            ],
        )


async def test_rejects_variants_on_services() -> None:
    with pytest.raises(ValidationError, match="variações"):
        await CreateCatalogItemUseCase(FakeCatalogItemRepository()).execute(
            name="Corte de cabelo",
            description=None,
            price_cents=3000,
            kind=CatalogItemKind.SERVICE,
            tracks_inventory=False,
            stock_quantity=None,
            variants=[ProductVariant(name="Longo")],
        )
