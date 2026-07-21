from datetime import datetime
from typing import Protocol

from app.domain.platform_sales.entities import PlatformSale


class PlatformSaleRepository(Protocol):
    """Persistência das vendas normalizadas, escopada por empresa (tenant)."""

    async def upsert(
        self,
        *,
        provider: str,
        external_id: str,
        product: str,
        amount_cents: int,
        occurred_at: datetime,
        is_refund: bool,
        buyer_name: str | None,
        buyer_email: str | None,
    ) -> bool:
        """Insere a venda se ainda não existir (idempotente por provider+external_id
        dentro da empresa). Retorna True se inseriu, False se já existia."""
        ...

    async def list_since(self, since: datetime | None) -> list[PlatformSale]:
        """Vendas da empresa a partir de `since` (ou todas, se None)."""
        ...
