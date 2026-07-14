from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class CatalogItemKind(StrEnum):
    PRODUCT = "product"
    SERVICE = "service"


@dataclass
class CatalogItem:
    """Um item vendável — produto (com estoque opcional) ou serviço (sem estoque).

    Produtos e serviços são unificados em uma única entidade, em vez de dois
    modelos quase idênticos, para evitar duplicação de CRUD; `kind` distingue
    o comportamento (só produtos podem rastrear estoque).
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


@dataclass
class StockMovement:
    id: str
    company_id: str
    item_id: str
    delta: int
    reason: str
    created_by: str
    created_at: datetime
