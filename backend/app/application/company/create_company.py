from app.core.exceptions import NotFoundError, ValidationError
from app.domain.company.cnpj import format_cnpj, is_valid_cnpj, normalize_cnpj
from app.domain.company.cnpj_lookup import CnpjInfo, CnpjLookup
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
        cnpj_lookup: CnpjLookup | None = None,
    ) -> None:
        self._company_repository = company_repository
        self._membership_repository = membership_repository
        # Opcional para não quebrar chamadas internas que já validaram o CNPJ.
        # Quando presente, o CNPJ é confrontado com a fonte externa.
        self._cnpj_lookup = cnpj_lookup

    async def validate_cnpj(self, raw: str) -> CnpjInfo | None:
        """Normaliza, valida os dígitos e confere se o CNPJ existe de verdade.

        Dígito verificador só prova que o número é bem formado — "11.222.333/
        0001-81" pode fechar a conta e não corresponder a empresa nenhuma. Sem a
        consulta externa, o cadastro aceita CNPJ inventado.
        """
        normalized = normalize_cnpj(raw)
        if not is_valid_cnpj(normalized):
            raise ValidationError("CNPJ inválido — confira os números digitados.")

        if self._cnpj_lookup is not None:
            try:
                info = await self._cnpj_lookup.fetch(normalized)
            except NotFoundError:
                raise ValidationError(
                    f"O CNPJ {format_cnpj(normalized)} não foi encontrado na base da Receita."
                ) from None
            # Falha da fonte externa (ConnectorError) sobe como está: é
            # indisponibilidade temporária, não CNPJ inválido, e a mensagem
            # precisa dizer isso para a pessoa tentar de novo em vez de achar
            # que digitou errado.
            if not info.is_active:
                situacao = info.status or "irregular"
                raise ValidationError(
                    f"O CNPJ {format_cnpj(normalized)} consta como {situacao} na Receita."
                )
            return info
        return None

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
        skip_cnpj_lookup: bool = False,
    ) -> Company:
        normalized_cnpj: str | None = None
        if cnpj and cnpj.strip():
            if skip_cnpj_lookup:
                # Quem chamou já validou (ex.: o cadastro). Repetir seria uma
                # segunda ida à Receita para a mesma resposta.
                normalized_cnpj = normalize_cnpj(cnpj)
            else:
                await self.validate_cnpj(cnpj)
                normalized_cnpj = normalize_cnpj(cnpj)

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
