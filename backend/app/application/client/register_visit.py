from datetime import UTC, datetime

from app.core.exceptions import NotFoundError
from app.domain.client.entities import Client
from app.domain.client.repository import ClientRepository


class RegisterClientVisitUseCase:
    """Marca o último atendimento do cliente como agora — base para calcular quando
    ele estará "na hora de voltar" (cadência de retorno)."""

    def __init__(self, client_repository: ClientRepository) -> None:
        self._client_repository = client_repository

    async def execute(self, *, client_id: str) -> Client:
        client = await self._client_repository.update(client_id, last_visit_at=datetime.now(UTC))
        if client is None:
            raise NotFoundError("Cliente não encontrado.")
        return client
