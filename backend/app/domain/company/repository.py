from typing import Protocol

from app.domain.company.entities import Company, CompanyMembership
from app.domain.company.roles import CompanyRole


class CompanyRepository(Protocol):
    async def create(
        self,
        *,
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
        currency: str = "BRL",
        sales_channels: list[str] | None = None,
        sales_mode: str | None = None,
        main_offerings: str | None = None,
        legal_name: str | None = None,
        trade_name: str | None = None,
        cnpj: str | None = None,
        subsegment: str | None = None,
        monthly_revenue_cents: int | None = None,
        phone: str | None = None,
        email: str | None = None,
        website: str | None = None,
        social_links: dict[str, str] | None = None,
    ) -> Company: ...

    async def get_by_id(self, company_id: str) -> Company | None: ...

    async def update(self, company_id: str, **fields: object) -> Company | None: ...

    async def delete(self, company_id: str) -> None: ...


class CompanyMembershipRepository(Protocol):
    async def create(
        self, *, company_id: str, user_id: str, role: CompanyRole
    ) -> CompanyMembership: ...

    async def get_by_user_and_company(
        self, user_id: str, company_id: str
    ) -> CompanyMembership | None: ...

    async def list_for_user(self, user_id: str) -> list[CompanyMembership]: ...

    async def delete(self, membership_id: str) -> None: ...
