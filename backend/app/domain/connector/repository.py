from datetime import datetime
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

    async def list_due_for_sync(self, *, older_than: datetime, limit: int) -> list[Connection]:
        """Conexões de TODAS as empresas que não sincronizam desde `older_than`.

        É o único ponto do sistema que atravessa o isolamento por empresa, e por
        isso o nome diz isso na cara. A justificativa: o agendador roda fora de
        requisição, sem usuário e sem empresa no contexto — ele não pode
        perguntar "as minhas conexões" porque não é de ninguém.

        Quem consome é obrigado a definir o contexto da empresa antes de tocar
        em qualquer dado dela; do contrário o vazamento entre inquilinos entraria
        justamente pela porta que existe para mantê-los sincronizados.
        """
        ...

    async def mark_synced(self, provider: str) -> None: ...

    async def mark_status(
        self, provider: str, *, status: ConnectionStatus, error: str | None
    ) -> None: ...

    async def delete(self, provider: str) -> bool: ...
