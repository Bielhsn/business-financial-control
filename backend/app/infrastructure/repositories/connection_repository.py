from datetime import UTC, datetime

from app.core.tenant import get_current_company_id
from app.domain.connector.entities import Connection, ConnectionStatus
from app.infrastructure.database.models.connection import ConnectionDocument


def _to_entity(document: ConnectionDocument) -> Connection:
    return Connection(
        id=str(document.id),
        company_id=document.company_id,
        provider=document.provider,
        status=ConnectionStatus(document.status),
        config=dict(document.config),
        last_synced_at=document.last_synced_at,
        last_error=document.last_error,
        created_at=document.created_at,
        updated_at=document.updated_at,
    )


class BeanieConnectionRepository:
    """Toda operação é automaticamente restrita à empresa do contexto de tenant atual."""

    async def upsert(
        self,
        *,
        provider: str,
        encrypted_secrets: str,
        config: dict[str, str],
    ) -> Connection:
        now = datetime.now(UTC)
        document = await self._get_document(provider)
        if document is None:
            document = ConnectionDocument(
                company_id=get_current_company_id(),
                provider=provider,
                status=ConnectionStatus.CONNECTED.value,
                encrypted_secrets=encrypted_secrets,
                config=config,
                created_at=now,
                updated_at=now,
            )
            await document.insert()
        else:
            document.encrypted_secrets = encrypted_secrets
            document.config = config
            document.status = ConnectionStatus.CONNECTED.value
            document.last_error = None
            document.updated_at = now
            await document.save()
        return _to_entity(document)

    async def get_by_provider(self, provider: str) -> Connection | None:
        document = await self._get_document(provider)
        return _to_entity(document) if document else None

    async def get_encrypted_secrets(self, provider: str) -> str | None:
        document = await self._get_document(provider)
        return document.encrypted_secrets if document else None

    async def list_all(self) -> list[Connection]:
        documents = await ConnectionDocument.find(
            {"company_id": get_current_company_id()}
        ).to_list()
        return [_to_entity(document) for document in documents]

    async def mark_synced(self, provider: str) -> None:
        document = await self._get_document(provider)
        if document is None:
            return
        document.last_synced_at = datetime.now(UTC)
        document.status = ConnectionStatus.CONNECTED.value
        document.last_error = None
        document.updated_at = datetime.now(UTC)
        await document.save()

    async def mark_status(
        self, provider: str, *, status: ConnectionStatus, error: str | None
    ) -> None:
        document = await self._get_document(provider)
        if document is None:
            return
        document.status = status.value
        document.last_error = error
        document.updated_at = datetime.now(UTC)
        await document.save()

    async def delete(self, provider: str) -> bool:
        document = await self._get_document(provider)
        if document is None:
            return False
        await document.delete()
        return True

    async def _get_document(self, provider: str) -> ConnectionDocument | None:
        return await ConnectionDocument.find_one(
            ConnectionDocument.company_id == get_current_company_id(),
            ConnectionDocument.provider == provider,
        )
