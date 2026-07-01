from app.core.exceptions import NotFoundError
from app.domain.financial.entities import FinancialCategory
from app.domain.financial.repository import FinancialCategoryRepository


class UpdateFinancialCategoryUseCase:
    def __init__(self, category_repository: FinancialCategoryRepository) -> None:
        self._category_repository = category_repository

    async def execute(self, *, category_id: str, **fields: object) -> FinancialCategory:
        clean_fields = {key: value for key, value in fields.items() if value is not None}
        if not clean_fields:
            category = await self._category_repository.get_by_id(category_id)
            if category is None:
                raise NotFoundError("Categoria financeira não encontrada.")
            return category

        category = await self._category_repository.update(category_id, **clean_fields)
        if category is None:
            raise NotFoundError("Categoria financeira não encontrada.")
        return category
