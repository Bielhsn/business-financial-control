from datetime import UTC, datetime

from pymongo.errors import DuplicateKeyError

from app.core.tenant import get_current_company_id
from app.domain.platform_sales.entities import PlatformSale
from app.infrastructure.database.models.platform_sale import PlatformSaleDocument


def _to_entity(document: PlatformSaleDocument) -> PlatformSale:
    return PlatformSale(
        id=str(document.id),
        company_id=document.company_id,
        provider=document.provider,
        external_id=document.external_id,
        product=document.product,
        amount_cents=document.amount_cents,
        occurred_at=document.occurred_at,
        is_refund=document.is_refund,
        buyer_name=document.buyer_name,
        buyer_email=document.buyer_email,
        created_at=document.created_at,
    )


class BeaniePlatformSaleRepository:
    """Escopado por empresa (tenant) via contexto atual."""

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
        company_id = get_current_company_id()
        existing = await PlatformSaleDocument.find_one(
            PlatformSaleDocument.company_id == company_id,
            PlatformSaleDocument.provider == provider,
            PlatformSaleDocument.external_id == external_id,
        )
        if existing is not None:
            return False
        document = PlatformSaleDocument(
            company_id=company_id,
            provider=provider,
            external_id=external_id,
            product=product,
            amount_cents=amount_cents,
            occurred_at=occurred_at,
            is_refund=is_refund,
            buyer_name=buyer_name,
            buyer_email=buyer_email,
            created_at=datetime.now(UTC),
        )
        try:
            await document.insert()
        except DuplicateKeyError:
            # Corrida entre dois syncs: o índice único garante idempotência.
            return False
        return True

    async def list_since(self, since: datetime | None) -> list[PlatformSale]:
        company_id = get_current_company_id()
        query = PlatformSaleDocument.find(PlatformSaleDocument.company_id == company_id)
        if since is not None:
            query = query.find(PlatformSaleDocument.occurred_at >= since)
        documents = await query.to_list()
        return [_to_entity(document) for document in documents]
