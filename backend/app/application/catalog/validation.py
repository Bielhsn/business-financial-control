"""Regras de validação compartilhadas entre criação e edição de itens do catálogo."""

from app.core.exceptions import ValidationError
from app.domain.catalog.entities import ProductVariant


def validate_pricing(
    *,
    price_cents: int,
    cost_price_cents: int | None,
    promo_price_cents: int | None,
) -> None:
    if price_cents <= 0:
        raise ValidationError("O preço deve ser maior que zero.")
    if cost_price_cents is not None and cost_price_cents < 0:
        raise ValidationError("O preço de custo não pode ser negativo.")
    if promo_price_cents is not None:
        if promo_price_cents <= 0:
            raise ValidationError("O preço promocional deve ser maior que zero.")
        if promo_price_cents >= price_cents:
            raise ValidationError("O preço promocional deve ser menor que o preço normal.")


def validate_stock_limits(*, min_stock: int | None, max_stock: int | None) -> None:
    if min_stock is not None and min_stock < 0:
        raise ValidationError("O estoque mínimo não pode ser negativo.")
    if max_stock is not None and max_stock < 0:
        raise ValidationError("O estoque máximo não pode ser negativo.")
    if min_stock is not None and max_stock is not None and min_stock > max_stock:
        raise ValidationError("O estoque mínimo não pode ser maior que o máximo.")


def validate_variants(variants: list[ProductVariant]) -> None:
    seen_names: set[str] = set()
    seen_skus: set[str] = set()
    for variant in variants:
        name = variant.name.strip().lower()
        if not name:
            raise ValidationError("Toda variação precisa de um nome (ex.: Azul / M).")
        if name in seen_names:
            raise ValidationError(f"Variação duplicada: {variant.name}.")
        seen_names.add(name)
        if variant.sku:
            sku = variant.sku.strip().lower()
            if sku in seen_skus:
                raise ValidationError(f"SKU de variação duplicado: {variant.sku}.")
            seen_skus.add(sku)
        if variant.price_cents is not None and variant.price_cents <= 0:
            raise ValidationError("O preço de uma variação deve ser maior que zero.")
        if variant.promo_price_cents is not None:
            if variant.promo_price_cents <= 0:
                raise ValidationError(
                    "O preço promocional de uma variação deve ser maior que zero."
                )
            reference_price = variant.price_cents
            if reference_price is not None and variant.promo_price_cents >= reference_price:
                raise ValidationError(
                    "O preço promocional de uma variação deve ser menor que o preço dela."
                )
        if variant.stock_quantity < 0:
            raise ValidationError("O estoque de uma variação não pode ser negativo.")
