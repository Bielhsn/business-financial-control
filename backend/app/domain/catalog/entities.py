from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class CatalogItemKind(StrEnum):
    PRODUCT = "product"
    SERVICE = "service"


@dataclass
class ProductVariant:
    """Uma combinação vendável do produto (ex.: "Azul / M").

    Preço/promoção `None` herdam os valores do produto pai — assim a maioria
    das variações não precisa repetir preço, só as exceções.
    """

    name: str
    sku: str | None = None
    barcode: str | None = None
    price_cents: int | None = None
    promo_price_cents: int | None = None
    stock_quantity: int = 0


@dataclass
class CatalogItem:
    """Um item vendável — produto (com estoque opcional) ou serviço (sem estoque).

    Produtos e serviços são unificados em uma única entidade, em vez de dois
    modelos quase idênticos, para evitar duplicação de CRUD; `kind` distingue
    o comportamento (só produtos podem rastrear estoque).

    Campos de catálogo profissional (SKU, imagens, variações, preços de custo/
    promoção) são todos opcionais: um serviço simples continua sendo criado só
    com nome + preço, enquanto um e-commerce pode preencher a ficha completa.
    """

    id: str
    company_id: str
    name: str
    description: str | None
    price_cents: int
    kind: CatalogItemKind
    tracks_inventory: bool
    stock_quantity: int | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    sku: str | None = None
    barcode: str | None = None
    brand: str | None = None
    supplier: str | None = None
    category: str | None = None
    subcategory: str | None = None
    short_description: str | None = None
    tags: list[str] = field(default_factory=list)
    cost_price_cents: int | None = None
    promo_price_cents: int | None = None
    min_stock: int | None = None
    max_stock: int | None = None
    stock_location: str | None = None
    images: list[str] = field(default_factory=list)
    variants: list[ProductVariant] = field(default_factory=list)


@dataclass
class StockMovement:
    id: str
    company_id: str
    item_id: str
    delta: int
    reason: str
    created_by: str
    created_at: datetime
