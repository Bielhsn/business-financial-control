from typing import Protocol

from app.domain.connector.entities import Connection, ConnectionStatus


class ConnectionRepository(Protocol):
    """Toda implementação filtra/carimba pela empresa do contexto de tenant atual.

    Segredos são recebidos/entregues já criptografados (string opaca) — o
    repositório não conhece o texto puro."""

    async def upsert(
        self,
        *,
        provider: str,
        encrypted_secrets: str,
        config: dict[str, str],
    ) -> Connection:
        """Cria ou atualiza a conexão da empresa com o provedor (uma por provedor)."""
        ...

    async def get_by_provider(self, provider: str) -> Connection | None: ...

    async def get_encrypted_secrets(self, provider: str) -> str | None: ...

    async def list_all(self) -> list[Connection]: ...

    async def mark_synced(self, provider: str) -> None: ...

    async def mark_status(
        self, provider: str, *, status: ConnectionStatus, error: str | None
    ) -> None: ...

    async def delete(self, provider: str) -> bool: ...
