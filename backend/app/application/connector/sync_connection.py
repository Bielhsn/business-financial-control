import json

from app.core.exceptions import ConnectorError, NotFoundError
from app.domain.connector.entities import ConnectionStatus, NormalizedSale, SyncResult
from app.domain.connector.ports import Connector, SecretCipher
from app.domain.connector.registry import get_connector_definition
from app.domain.connector.repository import ConnectionRepository
from app.domain.financial.entities import (
    FinancialCategory,
    FinancialCategoryType,
    TransactionStatus,
)
from app.domain.financial.repository import (
    FinancialCategoryRepository,
    FinancialTransactionRepository,
)


class SyncConnectionUseCase:
    """Puxa vendas/reembolsos do provedor e as materializa como lançamentos
    financeiros idempotentes (via `external_ref`), alimentando dashboard, fluxo
    de caixa e relatórios. Reutilizável por qualquer conector."""

    def __init__(
        self,
        connection_repository: ConnectionRepository,
        category_repository: FinancialCategoryRepository,
        transaction_repository: FinancialTransactionRepository,
        cipher: SecretCipher,
        connector: Connector,
    ) -> None:
        self._connection_repository = connection_repository
        self._category_repository = category_repository
        self._transaction_repository = transaction_repository
        self._cipher = cipher
        self._connector = connector

    async def execute(self, *, provider: str, created_by: str) -> SyncResult:
        connection = await self._connection_repository.get_by_provider(provider)
        if connection is None:
            raise NotFoundError("Conexão não encontrada.")

        encrypted = await self._connection_repository.get_encrypted_secrets(provider)
        secrets = json.loads(self._cipher.decrypt(encrypted)) if encrypted else {}
        credentials = {**secrets, **connection.config}

        try:
            sales = await self._connector.fetch_sales(credentials, since=connection.last_synced_at)
        except ConnectorError as exc:
            await self._connection_repository.mark_status(
                provider, status=ConnectionStatus.ERROR, error=exc.message
            )
            raise

        result = await self._import_sales(provider, sales, created_by)
        await self._connection_repository.mark_synced(provider)
        return result

    async def _import_sales(
        self, provider: str, sales: list[NormalizedSale], created_by: str
    ) -> SyncResult:
        definition = get_connector_definition(provider)
        provider_name = definition.name if definition else provider.capitalize()
        result = SyncResult()

        for sale in sales:
            external_ref = f"{provider}:{sale.external_id}"
            existing = await self._transaction_repository.find_by_external_ref(external_ref)
            if existing is not None:
                result.skipped += 1
                continue

            if sale.is_refund:
                tx_type = FinancialCategoryType.EXPENSE
                category_name = f"Reembolsos {provider_name}"
            else:
                tx_type = FinancialCategoryType.INCOME
                category_name = f"Vendas {provider_name}"

            category = await self._get_or_create_category(category_name, tx_type)
            notes_parts = [f"Importado de {provider_name}."]
            if sale.buyer_name:
                notes_parts.append(f"Cliente: {sale.buyer_name}")
            if sale.buyer_email:
                notes_parts.append(sale.buyer_email)

            await self._transaction_repository.create(
                category_id=category.id,
                type=tx_type,
                amount_cents=sale.amount_cents,
                description=sale.description,
                status=TransactionStatus.PAID,
                due_date=None,
                paid_at=sale.occurred_at,
                notes=" ".join(notes_parts),
                client_id=None,
                created_by=created_by,
                external_ref=external_ref,
            )
            result.imported += 1
            key = "refunds" if sale.is_refund else "sales"
            result.details[key] = result.details.get(key, 0) + 1

        return result

    async def _get_or_create_category(
        self, name: str, type: FinancialCategoryType
    ) -> FinancialCategory:
        category = await self._category_repository.get_by_name_and_type(name, type)
        if category is None:
            category = await self._category_repository.create(name=name, type=type)
        return category
