from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import Settings, get_settings
from app.core.exceptions import (
    AIProviderNotConfiguredError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
)
from app.core.tenant import CompanyContext, set_current_company_id
from app.domain.appointment.repository import AppointmentRepository
from app.domain.audit.repository import AuditLogRepository
from app.domain.auth.google import GoogleTokenVerifier
from app.domain.auth.ports import PasswordHasher, TokenService
from app.domain.auth.repository import RefreshTokenRepository
from app.domain.auth.verification import VerificationCodeRepository
from app.domain.blueprint.ports import AIProviderPort
from app.domain.blueprint.repository import CompanyBlueprintRepository
from app.domain.catalog.repository import CatalogItemRepository, StockMovementRepository
from app.domain.client.repository import ClientRepository
from app.domain.company.cnpj_lookup import CnpjLookup
from app.domain.company.repository import CompanyMembershipRepository, CompanyRepository
from app.domain.company.roles import CompanyRole
from app.domain.connector.ports import Connector, SecretCipher
from app.domain.connector.repository import ConnectionRepository
from app.domain.employee.repository import EmployeeRepository
from app.domain.financial.repository import (
    FinancialCategoryRepository,
    FinancialTransactionRepository,
)
from app.domain.notifications.email import EmailSender
from app.domain.user.entities import User
from app.domain.user.repository import UserRepository
from app.infrastructure.ai.anthropic_provider import AnthropicAIProvider
from app.infrastructure.auth.google import GoogleTokenInfoVerifier
from app.infrastructure.connectors.factory import build_connector
from app.infrastructure.email.console import ConsoleEmailSender
from app.infrastructure.external.brasilapi import BrasilApiCnpjLookup
from app.infrastructure.repositories.appointment_repository import BeanieAppointmentRepository
from app.infrastructure.repositories.audit_log_repository import BeanieAuditLogRepository
from app.infrastructure.repositories.catalog_item_repository import BeanieCatalogItemRepository
from app.infrastructure.repositories.client_repository import BeanieClientRepository
from app.infrastructure.repositories.company_blueprint_repository import (
    BeanieCompanyBlueprintRepository,
)
from app.infrastructure.repositories.company_membership_repository import (
    BeanieCompanyMembershipRepository,
)
from app.infrastructure.repositories.company_repository import BeanieCompanyRepository
from app.infrastructure.repositories.connection_repository import BeanieConnectionRepository
from app.infrastructure.repositories.employee_repository import BeanieEmployeeRepository
from app.infrastructure.repositories.financial_category_repository import (
    BeanieFinancialCategoryRepository,
)
from app.infrastructure.repositories.financial_transaction_repository import (
    BeanieFinancialTransactionRepository,
)
from app.infrastructure.repositories.refresh_token_repository import (
    BeanieRefreshTokenRepository,
)
from app.infrastructure.repositories.stock_movement_repository import (
    BeanieStockMovementRepository,
)
from app.infrastructure.repositories.user_repository import BeanieUserRepository
from app.infrastructure.repositories.verification_code_repository import (
    BeanieVerificationCodeRepository,
)
from app.infrastructure.security.crypto import FernetSecretCipher
from app.infrastructure.security.password import Argon2PasswordHasher
from app.infrastructure.security.tokens import JWTTokenService

_password_hasher = Argon2PasswordHasher()
# auto_error=False: preferimos levantar UnauthorizedError (401) nós mesmos, em vez do
# 403 que o HTTPBearer retorna por padrão quando o header Authorization está ausente.
_bearer_scheme = HTTPBearer(auto_error=False)


def get_user_repository() -> UserRepository:
    return BeanieUserRepository()


def get_refresh_token_repository() -> RefreshTokenRepository:
    return BeanieRefreshTokenRepository()


def get_password_hasher() -> PasswordHasher:
    return _password_hasher


def get_token_service(settings: Annotated[Settings, Depends(get_settings)]) -> TokenService:
    return JWTTokenService(settings)


def get_company_repository() -> CompanyRepository:
    return BeanieCompanyRepository()


def get_company_membership_repository() -> CompanyMembershipRepository:
    return BeanieCompanyMembershipRepository()


def get_company_blueprint_repository() -> CompanyBlueprintRepository:
    return BeanieCompanyBlueprintRepository()


def get_financial_category_repository() -> FinancialCategoryRepository:
    return BeanieFinancialCategoryRepository()


def get_financial_transaction_repository() -> FinancialTransactionRepository:
    return BeanieFinancialTransactionRepository()


def get_client_repository() -> ClientRepository:
    return BeanieClientRepository()


def get_catalog_item_repository() -> CatalogItemRepository:
    return BeanieCatalogItemRepository()


def get_stock_movement_repository() -> StockMovementRepository:
    return BeanieStockMovementRepository()


def get_employee_repository() -> EmployeeRepository:
    return BeanieEmployeeRepository()


def get_appointment_repository() -> AppointmentRepository:
    return BeanieAppointmentRepository()


def get_connection_repository() -> ConnectionRepository:
    return BeanieConnectionRepository()


def get_secret_cipher(settings: Annotated[Settings, Depends(get_settings)]) -> SecretCipher:
    return FernetSecretCipher(settings)


def get_connector_factory() -> Callable[[str], Connector]:
    # Injetável para que os testes substituam por um conector fake (sem rede).
    return build_connector


def get_cnpj_lookup() -> CnpjLookup:
    return BrasilApiCnpjLookup()


def get_verification_code_repository() -> VerificationCodeRepository:
    return BeanieVerificationCodeRepository()


def get_email_sender(settings: Annotated[Settings, Depends(get_settings)]) -> EmailSender:
    # Só o adaptador de console por ora; SMTP/provedor real pluga aqui via settings.
    return ConsoleEmailSender()


def get_google_verifier(
    settings: Annotated[Settings, Depends(get_settings)],
) -> GoogleTokenVerifier:
    if not settings.google_client_id:
        raise AIProviderNotConfiguredError(
            "Login com Google indisponível: defina GOOGLE_CLIENT_ID."
        )
    return GoogleTokenInfoVerifier(client_id=settings.google_client_id)


def get_ai_provider(settings: Annotated[Settings, Depends(get_settings)]) -> AIProviderPort:
    if settings.ai_provider != "anthropic":
        raise AIProviderNotConfiguredError(
            f"Provedor de IA '{settings.ai_provider}' não é suportado."
        )
    if not settings.anthropic_api_key:
        raise AIProviderNotConfiguredError(
            "Defina ANTHROPIC_API_KEY para habilitar a geração de blueprint por IA."
        )
    return AnthropicAIProvider(settings)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
    token_service: Annotated[TokenService, Depends(get_token_service)],
) -> User:
    if credentials is None:
        raise UnauthorizedError("Credenciais não fornecidas.")

    payload = token_service.decode_access_token(credentials.credentials)
    user_id = payload.get("sub")
    if not isinstance(user_id, str):
        raise UnauthorizedError("Token inválido.")

    user = await user_repository.get_by_id(user_id)
    if user is None or not user.is_active:
        raise UnauthorizedError("Usuário inválido ou inativo.")
    return user


async def get_company_context(
    company_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    membership_repository: Annotated[
        CompanyMembershipRepository, Depends(get_company_membership_repository)
    ],
) -> CompanyContext:
    membership = await membership_repository.get_by_user_and_company(current_user.id, company_id)
    if membership is None:
        # 404, não 403: não revela a quem não tem acesso se a empresa existe.
        raise NotFoundError("Empresa não encontrada.")

    set_current_company_id(company_id)
    return CompanyContext(company_id=company_id, role=membership.role)


def require_role(
    *allowed_roles: CompanyRole,
) -> Callable[[CompanyContext], Awaitable[CompanyContext]]:
    async def _dependency(
        company_context: Annotated[CompanyContext, Depends(get_company_context)],
    ) -> CompanyContext:
        if company_context.role not in allowed_roles:
            raise ForbiddenError("Você não tem permissão para esta ação.")
        return company_context

    return _dependency


def get_audit_log_repository() -> AuditLogRepository:
    return BeanieAuditLogRepository()
