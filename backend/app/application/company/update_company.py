from app.core.exceptions import NotFoundError
from app.domain.company.entities import Company
from app.domain.company.repository import CompanyRepository


class UpdateCompanyUseCase:
    def __init__(self, company_repository: CompanyRepository) -> None:
        self._company_repository = company_repository

    async def execute(self, *, company_id: str, **fields: object) -> Company:
        clean_fields = {key: value for key, value in fields.items() if value is not None}
        if not clean_fields:
            company = await self._company_repository.get_by_id(company_id)
            if company is None:
                raise NotFoundError("Empresa não encontrada.")
            return company

        company = await self._company_repository.update(company_id, **clean_fields)
        if company is None:
            raise NotFoundError("Empresa não encontrada.")
        return company
