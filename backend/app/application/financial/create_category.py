from app.core.exceptions import ConflictError
from app.domain.financial.entities import FinancialCategory, FinancialCategoryType
from app.domain.financial.repository import FinancialCategoryRepository


class CreateFinancialCategoryUseCase:
    def __init__(self, category_repository: FinancialCategoryRepository) -> None:
        self._category_repository = category_repository

    async def execute(self, *, name: str, type: FinancialCategoryType) -> FinancialCategory:
        normalized_name = name.strip()
        existing = await self._category_repository.get_by_name_and_type(normalized_name, type)
        if existing is not None:
            raise ConflictError("Já existe uma categoria com este nome e tipo.")
        return await self._category_repository.create(name=normalized_name, type=type)
