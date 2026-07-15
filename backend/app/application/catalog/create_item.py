from app.application.catalog.validation import (
    validate_pricing,
    validate_stock_limits,
    validate_variants,
)
from app.core.exceptions import ValidationError
from app.domain.catalog.entities import CatalogItem, CatalogItemKind, ProductVariant
from app.domain.catalog.repository import CatalogItemRepository


class CreateCatalogItemUseCase:
    def __init__(self, item_repository: CatalogItemRepository) -> None:
        self._item_repository = item_repository

    async def execute(
        self,
        *,
        name: str,
        description: str | None,
        price_cents: int,
        kind: CatalogItemKind,
        tracks_inventory: bool,
        stock_quantity: int | None,
        sku: str | None = None,
        barcode: str | None = None,
        brand: str | None = None,
        supplier: str | None = None,
        category: str | None = None,
        subcategory: str | None = None,
        short_description: str | None = None,
        tags: list[str] | None = None,
        cost_price_cents: int | None = None,
        promo_price_cents: int | None = None,
        min_stock: int | None = None,
        max_stock: int | None = None,
        stock_location: str | None = None,
        images: list[str] | None = None,
        variants: list[ProductVariant] | None = None,
    ) -> CatalogItem:
        validate_pricing(
            price_cents=price_cents,
            cost_price_cents=cost_price_cents,
            promo_price_cents=promo_price_cents,
        )
        validate_stock_limits(min_stock=min_stock, max_stock=max_stock)
        variants = variants or []
        validate_variants(variants)

        if kind == CatalogItemKind.SERVICE:
            if tracks_inventory:
                raise ValidationError("Serviços não controlam estoque.")
            if variants:
                raise ValidationError("Serviços não têm variações.")
            stock_quantity = None
        elif tracks_inventory:
            stock_quantity = stock_quantity if stock_quantity is not None else 0
            if stock_quantity < 0:
                raise ValidationError("O estoque inicial não pode ser negativo.")
        else:
            stock_quantity = None

        sku = sku.strip() if sku else None
        if sku:
            existing = await self._item_repository.find_by_sku(sku)
            if existing is not None:
                raise ValidationError(f"Já existe um item com o SKU {sku}.")

        return await self._item_repository.create(
            name=name.strip(),
            description=description.strip() if description else None,
            price_cents=price_cents,
            kind=kind,
            tracks_inventory=tracks_inventory,
            stock_quantity=stock_quantity,
            sku=sku,
            barcode=barcode.strip() if barcode else None,
            brand=brand.strip() if brand else None,
            supplier=supplier.strip() if supplier else None,
            category=category.strip() if category else None,
            subcategory=subcategory.strip() if subcategory else None,
            short_description=short_description.strip() if short_description else None,
            tags=[tag.strip() for tag in (tags or []) if tag.strip()],
            cost_price_cents=cost_price_cents,
            promo_price_cents=promo_price_cents,
            min_stock=min_stock,
            max_stock=max_stock,
            stock_location=stock_location.strip() if stock_location else None,
            images=images or [],
            variants=variants,
        )
