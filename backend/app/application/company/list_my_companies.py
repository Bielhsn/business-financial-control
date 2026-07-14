from dataclasses import dataclass

from app.domain.company.entities import Company
from app.domain.company.repository import CompanyMembershipRepository, CompanyRepository
from app.domain.company.roles import CompanyRole


@dataclass
class CompanyWithRole:
    company: Company
    role: CompanyRole


class ListMyCompaniesUseCase:
    def __init__(
        self,
        membership_repository: CompanyMembershipRepository,
        company_repository: CompanyRepository,
    ) -> None:
        self._membership_repository = membership_repository
        self._company_repository = company_repository

    async def execute(self, *, user_id: str) -> list[CompanyWithRole]:
        memberships = await self._membership_repository.list_for_user(user_id)

        results: list[CompanyWithRole] = []
        for membership in memberships:
            company = await self._company_repository.get_by_id(membership.company_id)
            if company is not None and company.is_active:
                results.append(CompanyWithRole(company=company, role=membership.role))
        return results
