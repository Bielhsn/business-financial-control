from app.application.client._custom_fields import validate_custom_fields
from app.domain.blueprint.repository import CompanyBlueprintRepository
from app.domain.client.entities import Client
from app.domain.client.repository import ClientRepository


class CreateClientUseCase:
    def __init__(
        self,
        client_repository: ClientRepository,
        blueprint_repository: CompanyBlueprintRepository,
    ) -> None:
        self._client_repository = client_repository
        self._blueprint_repository = blueprint_repository

    async def execute(
        self,
        *,
        company_id: str,
        name: str,
        email: str | None,
        phone: str | None,
        notes: str | None,
        custom_fields: dict[str, str],
    ) -> Client:
        await validate_custom_fields(
            company_id=company_id,
            custom_fields=custom_fields,
            blueprint_repository=self._blueprint_repository,
        )
        return await self._client_repository.create(
            name=name.strip(),
            email=email,
            phone=phone,
            notes=notes.strip() if notes else None,
            custom_fields=custom_fields,
        )
