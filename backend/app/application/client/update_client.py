from app.application.client._custom_fields import validate_custom_fields
from app.core.exceptions import NotFoundError
from app.domain.blueprint.repository import CompanyBlueprintRepository
from app.domain.client.entities import Client
from app.domain.client.repository import ClientRepository


class UpdateClientUseCase:
    def __init__(
        self,
        client_repository: ClientRepository,
        blueprint_repository: CompanyBlueprintRepository,
    ) -> None:
        self._client_repository = client_repository
        self._blueprint_repository = blueprint_repository

    async def execute(self, *, company_id: str, client_id: str, **fields: object) -> Client:
        clean_fields = {key: value for key, value in fields.items() if value is not None}

        custom_fields = clean_fields.get("custom_fields")
        if isinstance(custom_fields, dict):
            await validate_custom_fields(
                company_id=company_id,
                custom_fields=custom_fields,
                blueprint_repository=self._blueprint_repository,
            )

        if not clean_fields:
            client = await self._client_repository.get_by_id(client_id)
            if client is None:
                raise NotFoundError("Cliente não encontrado.")
            return client

        client = await self._client_repository.update(client_id, **clean_fields)
        if client is None:
            raise NotFoundError("Cliente não encontrado.")
        return client
