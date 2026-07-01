from app.domain.company.entities import Company
from app.domain.company.repository import CompanyMembershipRepository, CompanyRepository
from app.domain.company.roles import CompanyRole


class CreateCompanyUseCase:
    """Cria a empresa e vincula o criador como OWNER.

    Sem transação multi-documento (compatível com MongoDB standalone, usado em
    desenvolvimento). Em um cluster com replica set (ex.: Atlas, sempre replica
    set) isso pode evoluir para uma transação real; por ora, uma ação
    compensatória (excluir a empresa) evita registros órfãos se o vínculo falhar.
    """

    def __init__(
        self,
        company_repository: CompanyRepository,
        membership_repository: CompanyMembershipRepository,
    ) -> None:
        self._company_repository = company_repository
        self._membership_repository = membership_repository

    async def execute(
        self,
        *,
        owner_id: str,
        name: str,
        segment: str,
        employee_count: int,
        average_customer_count: int,
        city: str,
        state: str,
        country: str,
        size: str,
        tax_regime: str | None,
        additional_info: str | None,
    ) -> Company:
        company = await self._company_repository.create(
            name=name.strip(),
            segment=segment.strip(),
            employee_count=employee_count,
            average_customer_count=average_customer_count,
            city=city.strip(),
            state=state.strip(),
            country=country.strip(),
            size=size.strip(),
            tax_regime=tax_regime.strip() if tax_regime else None,
            additional_info=additional_info.strip() if additional_info else None,
        )

        try:
            await self._membership_repository.create(
                company_id=company.id, user_id=owner_id, role=CompanyRole.OWNER
            )
        except Exception:
            await self._company_repository.delete(company.id)
            raise

        return company
