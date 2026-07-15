from app.application.catalog.validation import (
    validate_pricing,
    validate_stock_limits,
    validate_variants,
)
from app.core.exceptions import NotFoundError, ValidationError
from app.domain.catalog.entities import CatalogItem, ProductVariant
from app.domain.catalog.repository import CatalogItemRepository


class UpdateCatalogItemUseCase:
    """Não altera `stock_quantity` diretamente — ajustes de estoque passam por
    `AdjustStockUseCase`, para manter o registro de auditoria (`StockMovement`).

    Campos ausentes (None) são ignorados; listas vazias são gravadas (permitem
    limpar tags, imagens e variações)."""

    def __init__(self, item_repository: CatalogItemRepository) -> None:
        self._item_repository = item_repository

    async def execute(self, *, item_id: str, **fields: object) -> CatalogItem:
        clean_fields = {key: value for key, value in fields.items() if value is not None}

        current = await self._item_repository.get_by_id(item_id)
        if current is None:
            raise NotFoundError("Item de catálogo não encontrado.")

        # Valida a combinação final (valor novo quando enviado, atual caso contrário),
        # para que promo/custo/limites continuem coerentes após edições parciais.
        price = clean_fields.get("price_cents", current.price_cents)
        cost = clean_fields.get("cost_price_cents", current.cost_price_cents)
        promo = clean_fields.get("promo_price_cents", current.promo_price_cents)
        if not isinstance(price, int):
            raise ValidationError("O preço deve ser um número inteiro de centavos.")
        validate_pricing(
            price_cents=price,
            cost_price_cents=cost if isinstance(cost, int) else None,
            promo_price_cents=promo if isinstance(promo, int) else None,
        )

        min_stock = clean_fields.get("min_stock", current.min_stock)
        max_stock = clean_fields.get("max_stock", current.max_stock)
        validate_stock_limits(
            min_stock=min_stock if isinstance(min_stock, int) else None,
            max_stock=max_stock if isinstance(max_stock, int) else None,
        )

        variants = clean_fields.get("variants")
        if isinstance(variants, list):
            typed_variants = [v for v in variants if isinstance(v, ProductVariant)]
            validate_variants(typed_variants)

        sku = clean_fields.get("sku")
        if isinstance(sku, str):
            sku = sku.strip()
            clean_fields["sku"] = sku
            if sku and sku != (current.sku or ""):
                existing = await self._item_repository.find_by_sku(sku)
                if existing is not None and existing.id != item_id:
                    raise ValidationError(f"Já existe um item com o SKU {sku}.")

        if not clean_fields:
            return current

        item = await self._item_repository.update(item_id, **clean_fields)
        if item is None:
            raise NotFoundError("Item de catálogo não encontrado.")
        return item
