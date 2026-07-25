from typing import Protocol

from app.domain.client.entities import Client


class ClientRepository(Protocol):
    """Toda implementação filtra/carimba pela empresa do contexto de tenant atual."""

    async def create(
        self,
        *,
        name: str,
        email: str | None,
        phone: str | None,
        notes: str | None,
        custom_fields: dict[str, str],
        return_interval_days: int | None = None,
    ) -> Client: ...

    async def get_by_id(self, client_id: str) -> Client | None: ...

    async def list_all(self, *, only_active: bool = True) -> list[Client]: ...

    async def update(self, client_id: str, **fields: object) -> Client | None: ...
