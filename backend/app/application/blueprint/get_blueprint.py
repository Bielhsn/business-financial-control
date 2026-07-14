from app.core.exceptions import NotFoundError
from app.domain.blueprint.entities import CompanyBlueprint
from app.domain.blueprint.repository import CompanyBlueprintRepository


class GetCompanyBlueprintUseCase:
    def __init__(self, blueprint_repository: CompanyBlueprintRepository) -> None:
        self._blueprint_repository = blueprint_repository

    async def execute(self, *, company_id: str) -> CompanyBlueprint:
        blueprint = await self._blueprint_repository.get_by_company_id(company_id)
        if blueprint is None:
            raise NotFoundError("Esta empresa ainda não possui um blueprint gerado.")
        return blueprint
