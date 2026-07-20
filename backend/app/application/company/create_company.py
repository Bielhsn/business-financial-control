from app.core.exceptions import ValidationError
from app.domain.company.cnpj import is_valid_cnpj, normalize_cnpj
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
    ) -> Company:
        normalized_cnpj: str | None = None
        if cnpj and cnpj.strip():
            normalized_cnpj = normalize_cnpj(cnpj)
            if not is_valid_cnpj(normalized_cnpj):
                raise ValidationError("CNPJ inválido.")

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
            currency=currency.strip().upper(),
            sales_channels=[c.strip() for c in (sales_channels or []) if c.strip()],
            sales_mode=sales_mode.strip() if sales_mode else None,
            main_offerings=main_offerings.strip() if main_offerings else None,
            legal_name=legal_name.strip() if legal_name else None,
            trade_name=trade_name.strip() if trade_name else None,
            cnpj=normalized_cnpj,
            subsegment=subsegment.strip() if subsegment else None,
            monthly_revenue_cents=monthly_revenue_cents,
            phone=phone.strip() if phone else None,
            email=email.strip() if email else None,
            website=website.strip() if website else None,
            social_links={k: v.strip() for k, v in (social_links or {}).items() if v.strip()},
        )

        try:
            await self._membership_repository.create(
                company_id=company.id, user_id=owner_id, role=CompanyRole.OWNER
            )
        except Exception:
            await self._company_repository.delete(company.id)
            raise

        return company
