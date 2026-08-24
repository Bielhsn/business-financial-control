"""Cadastro completo: a conta do responsável e a primeira empresa, juntas.

Antes eram dois passos desconectados. A conta nascia sozinha e a empresa vinha
depois, no onboarding — quem abandonasse o meio do caminho ficava com um login
que não levava a lugar nenhum, e o suporte não tinha como saber de que empresa
aquela pessoa era.

**A ordem das operações é a parte que importa.** Tudo que pode ser recusado é
verificado ANTES de gravar qualquer coisa: senha, CNPJ (formato, existência,
situação) e as duas unicidades. Validar no fim deixaria uma conta órfã toda vez
que o CNPJ fosse recusado — usuário criado, empresa não.

Como a criação da empresa ainda pode falhar por corrida (duas requisições com o
mesmo CNPJ passando juntas pela verificação), existe a ação compensatória:
remover o usuário recém-criado em vez de deixá-lo sem empresa.
"""

from app.application.company.create_company import CreateCompanyUseCase
from app.core.config import Settings
from app.core.exceptions import ConflictError
from app.core.logging import get_logger
from app.domain.auth.ports import PasswordHasher
from app.domain.company.cnpj import format_cnpj, normalize_cnpj
from app.domain.company.cnpj_lookup import CnpjLookup
from app.domain.company.entities import Company
from app.domain.company.repository import CompanyRepository
from app.domain.user.entities import User
from app.domain.user.repository import UserRepository

logger = get_logger(__name__)

# Placeholders do que o onboarding preenche depois. Segmento vazio resolve para
# o perfil genérico, que não declara capacidade nenhuma — a empresa começa
# neutra e ganha identidade quando o dono informa o ramo.
_PENDING_SEGMENT = ""
_PENDING_SIZE = ""


class RegisterAccountUseCase:
    def __init__(
        self,
        user_repository: UserRepository,
        company_repository: CompanyRepository,
        create_company: CreateCompanyUseCase,
        password_hasher: PasswordHasher,
        cnpj_lookup: CnpjLookup,
        settings: Settings,
    ) -> None:
        self._users = user_repository
        self._companies = company_repository
        self._create_company = create_company
        self._hasher = password_hasher
        self._cnpj_lookup = cnpj_lookup
        self._settings = settings

    async def execute(
        self,
        *,
        email: str,
        password: str,
        full_name: str,
        company_name: str,
        cnpj: str,
        phone: str | None = None,
        job_role: str | None = None,
    ) -> tuple[User, Company]:
        normalized_email = email.strip().lower()
        normalized_cnpj = normalize_cnpj(cnpj)

        # --- Tudo que recusa, antes de gravar qualquer coisa ---
        if await self._users.get_by_email(normalized_email) is not None:
            raise ConflictError("Já existe uma conta com este e-mail.")
        if await self._companies.get_by_cnpj(normalized_cnpj) is not None:
            raise ConflictError(
                f"O CNPJ {format_cnpj(normalized_cnpj)} já está cadastrado em outra conta."
            )
        # Confronta com a Receita: valida formato, existência e situação. Erro
        # de indisponibilidade sobe como está — é temporário, e tratá-lo como
        # CNPJ inválido faria a pessoa conferir números que estão certos.
        info = await self._create_company.validate_cnpj(normalized_cnpj)

        # --- A partir daqui, grava ---
        user = await self._users.create(
            email=normalized_email,
            hashed_password=self._hasher.hash(password),
            full_name=full_name.strip(),
            is_verified=not self._settings.require_email_verification,
            phone=phone.strip() if phone else None,
            job_role=job_role.strip() if job_role else None,
        )

        try:
            company = await self._create_company.execute(
                owner_id=user.id,
                name=company_name.strip(),
                cnpj=normalized_cnpj,
                # Cidade, estado e razão social vêm da Receita — o dono não
                # redigita o que a consulta já trouxe.
                city=(info.city if info else None) or "",
                state=(info.state if info else None) or "",
                legal_name=info.legal_name if info else None,
                trade_name=info.trade_name if info else None,
                country="Brasil",
                # O onboarding preenche o resto. Segmento vazio resolve para o
                # perfil genérico, que não declara capacidade nenhuma: a empresa
                # começa neutra e ganha identidade quando o dono informa o ramo.
                segment=_PENDING_SEGMENT,
                size=_PENDING_SIZE,
                employee_count=0,
                average_customer_count=0,
                tax_regime=None,
                additional_info=None,
                # `validate_cnpj` já confirmou o CNPJ; repetir seria uma segunda
                # ida à Receita para a mesma resposta.
                skip_cnpj_lookup=True,
            )
        except Exception:
            # Corrida no CNPJ (duas requisições passando juntas pela
            # verificação) ou falha ao vincular o dono. Sem isto, sobraria uma
            # conta sem empresa — exatamente o estado que este fluxo existe para
            # evitar.
            logger.warning("register_rollback_user", email=normalized_email)
            await self._users.delete(user.id)
            raise

        return user, company
