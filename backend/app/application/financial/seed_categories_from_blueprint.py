from app.core.exceptions import NotFoundError
from app.domain.blueprint.repository import CompanyBlueprintRepository
from app.domain.financial.entities import FinancialCategory
from app.domain.financial.repository import FinancialCategoryRepository


class SeedFinancialCategoriesFromBlueprintUseCase:
    """Importa como categorias reais as sugestões do Company Blueprint (Etapa 4).

    Idempotente: categorias já existentes (mesmo nome e tipo) não são duplicadas.
    """

    def __init__(
        self,
        blueprint_repository: CompanyBlueprintRepository,
        category_repository: FinancialCategoryRepository,
    ) -> None:
        self._blueprint_repository = blueprint_repository
        self._category_repository = category_repository

    async def execute(self, *, company_id: str) -> list[FinancialCategory]:
        blueprint = await self._blueprint_repository.get_by_company_id(company_id)
        if blueprint is None:
            raise NotFoundError("Gere o blueprint da empresa antes de importar categorias.")

        existing = await self._category_repository.list_all(only_active=False)
        existing_keys = {(category.name.lower(), category.type) for category in existing}

        created: list[FinancialCategory] = []
        for suggestion in blueprint.financial_categories:
            key = (suggestion.name.lower(), suggestion.type)
            if key in existing_keys:
                continue
            category = await self._category_repository.create(
                name=suggestion.name, type=suggestion.type
            )
            created.append(category)
            existing_keys.add(key)

        return created
