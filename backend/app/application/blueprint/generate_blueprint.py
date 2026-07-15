from app.core.exceptions import NotFoundError
from app.domain.blueprint.entities import CompanyBlueprint
from app.domain.blueprint.ports import AIProviderPort
from app.domain.blueprint.repository import CompanyBlueprintRepository
from app.domain.company.repository import CompanyRepository


class GenerateCompanyBlueprintUseCase:
    def __init__(
        self,
        company_repository: CompanyRepository,
        blueprint_repository: CompanyBlueprintRepository,
        ai_provider: AIProviderPort,
        ai_provider_name: str,
    ) -> None:
        self._company_repository = company_repository
        self._blueprint_repository = blueprint_repository
        self._ai_provider = ai_provider
        self._ai_provider_name = ai_provider_name

    async def execute(self, *, company_id: str, additional_context: str | None) -> CompanyBlueprint:
        company = await self._company_repository.get_by_id(company_id)
        if company is None:
            raise NotFoundError("Empresa não encontrada.")

        draft = await self._ai_provider.generate_company_blueprint(
            company=company, additional_context=additional_context
        )

        return await self._blueprint_repository.upsert(
            company_id=company_id,
            modules=draft.modules,
            financial_categories=draft.financial_categories,
            kpis=draft.kpis,
            client_custom_fields=draft.client_custom_fields,
            ai_provider=self._ai_provider_name,
            integrations=draft.integrations,
        )
