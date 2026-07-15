from datetime import UTC, datetime

from beanie import PydanticObjectId
from beanie.operators import Inc, Set

from app.core.tenant import get_current_company_id
from app.domain.catalog.entities import CatalogItem, CatalogItemKind, ProductVariant
from app.infrastructure.database.models.catalog_item import (
    CatalogItemDocument,
    ProductVariantModel,
)


def _variant_to_entity(model: ProductVariantModel) -> ProductVariant:
    return ProductVariant(
        name=model.name,
        sku=model.sku,
        barcode=model.barcode,
        price_cents=model.price_cents,
        promo_price_cents=model.promo_price_cents,
        stock_quantity=model.stock_quantity,
    )


def _variant_to_model(variant: ProductVariant) -> ProductVariantModel:
    return ProductVariantModel(
        name=variant.name,
        sku=variant.sku,
        barcode=variant.barcode,
        price_cents=variant.price_cents,
        promo_price_cents=variant.promo_price_cents,
        stock_quantity=variant.stock_quantity,
    )


def _to_entity(document: CatalogItemDocument) -> CatalogItem:
    return CatalogItem(
        id=str(document.id),
        company_id=document.company_id,
        name=document.name,
        description=document.description,
        price_cents=document.price_cents,
        kind=CatalogItemKind(document.kind),
        tracks_inventory=document.tracks_inventory,
        stock_quantity=document.stock_quantity,
        is_active=document.is_active,
        created_at=document.created_at,
        updated_at=document.updated_at,
        sku=document.sku,
        barcode=document.barcode,
        brand=document.brand,
        supplier=document.supplier,
        category=document.category,
        subcategory=document.subcategory,
        short_description=document.short_description,
        tags=list(document.tags),
        cost_price_cents=document.cost_price_cents,
        promo_price_cents=document.promo_price_cents,
        min_stock=document.min_stock,
        max_stock=document.max_stock,
        stock_location=document.stock_location,
        images=list(document.images),
        variants=[_variant_to_entity(variant) for variant in document.variants],
    )


class BeanieCatalogItemRepository:
    """Toda operação é automaticamente restrita à empresa do contexto de tenant atual."""

    async def create(
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
        now = datetime.now(UTC)
        document = CatalogItemDocument(
            company_id=get_current_company_id(),
            name=name,
            description=description,
            price_cents=price_cents,
            kind=kind.value,
            tracks_inventory=tracks_inventory,
            stock_quantity=stock_quantity,
            sku=sku,
            barcode=barcode,
            brand=brand,
            supplier=supplier,
            category=category,
            subcategory=subcategory,
            short_description=short_description,
            tags=tags or [],
            cost_price_cents=cost_price_cents,
            promo_price_cents=promo_price_cents,
            min_stock=min_stock,
            max_stock=max_stock,
            stock_location=stock_location,
            images=images or [],
            variants=[_variant_to_model(variant) for variant in (variants or [])],
            created_at=now,
            updated_at=now,
        )
        await document.insert()
        return _to_entity(document)

    async def get_by_id(self, item_id: str) -> CatalogItem | None:
        if not PydanticObjectId.is_valid(item_id):
            return None
        document = await CatalogItemDocument.find_one(
            CatalogItemDocument.id == PydanticObjectId(item_id),
            CatalogItemDocument.company_id == get_current_company_id(),
        )
        return _to_entity(document) if document else None

    async def find_by_sku(self, sku: str) -> CatalogItem | None:
        document = await CatalogItemDocument.find_one(
            CatalogItemDocument.sku == sku,
            CatalogItemDocument.company_id == get_current_company_id(),
        )
        return _to_entity(document) if document else None

    async def list_all(self, *, only_active: bool = True) -> list[CatalogItem]:
        query: dict[str, object] = {"company_id": get_current_company_id()}
        if only_active:
            query["is_active"] = True
        documents = await CatalogItemDocument.find(query).to_list()
        return [_to_entity(document) for document in documents]

    async def update(self, item_id: str, **fields: object) -> CatalogItem | None:
        document = await self._get_document(item_id)
        if document is None:
            return None
        for field_name, value in fields.items():
            if field_name == "variants" and isinstance(value, list):
                value = [
                    _variant_to_model(variant)
                    for variant in value
                    if isinstance(variant, ProductVariant)
                ]
            setattr(document, field_name, value)
        document.updated_at = datetime.now(UTC)
        await document.save()
        return _to_entity(document)

    async def adjust_stock(self, item_id: str, *, delta: int) -> CatalogItem | None:
        document = await self._get_document(item_id)
        if document is None:
            return None
        # Atômico ($inc + $set em uma única operação) — evita condição de corrida
        # entre ler o estoque atual e gravar o novo valor sob ajustes concorrentes.
        await document.update(
            Inc({CatalogItemDocument.stock_quantity: delta}),  # type: ignore[no-untyped-call]
            Set({CatalogItemDocument.updated_at: datetime.now(UTC)}),  # type: ignore[no-untyped-call]
        )
        return _to_entity(document)

    async def _get_document(self, item_id: str) -> CatalogItemDocument | None:
        if not PydanticObjectId.is_valid(item_id):
            return None
        return await CatalogItemDocument.find_one(
            CatalogItemDocument.id == PydanticObjectId(item_id),
            CatalogItemDocument.company_id == get_current_company_id(),
        )
