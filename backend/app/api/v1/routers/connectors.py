from collections.abc import Callable
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.v1.deps import (
    get_audit_log_repository,
    get_company_context,
    get_connection_repository,
    get_connector_factory,
    get_current_user,
    get_financial_category_repository,
    get_financial_transaction_repository,
    get_secret_cipher,
    get_subscription_repository,
    require_role,
)
from app.application.connector.connect_provider import ConnectProviderUseCase
from app.application.connector.sync_connection import SyncConnectionUseCase
from app.application.subscription.gating import ensure_can_add_integration
from app.core.audit import record_audit
from app.core.exceptions import NotFoundError
from app.core.tenant import CompanyContext
from app.domain.audit.repository import AuditLogRepository
from app.domain.company.roles import CompanyRole
from app.domain.connector.entities import Connection
from app.domain.connector.ports import Connector, SecretCipher
from app.domain.connector.registry import CONNECTOR_REGISTRY
from app.domain.connector.repository import ConnectionRepository
from app.domain.financial.repository import (
    FinancialCategoryRepository,
    FinancialTransactionRepository,
)
from app.domain.subscription.repository import SubscriptionRepository
from app.domain.user.entities import User
from app.schemas.connector import (
    AvailableConnectorsResponse,
    ConnectionResponse,
    ConnectorDefinitionResponse,
    ConnectRequest,
    CredentialFieldResponse,
    SyncResultResponse,
)

router = APIRouter(prefix="/companies/{company_id}/connectors", tags=["connectors"])

_MANAGEMENT_ROLES = (CompanyRole.OWNER, CompanyRole.ADMIN, CompanyRole.MANAGER)


def _to_connection_response(connection: Connection) -> ConnectionResponse:
    return ConnectionResponse(
        id=connection.id,
        company_id=connection.company_id,
        provider=connection.provider,
        status=connection.status,
        config=connection.config,
        last_synced_at=connection.last_synced_at,
        last_error=connection.last_error,
        created_at=connection.created_at,
        updated_at=connection.updated_at,
    )


@router.get("/available", response_model=AvailableConnectorsResponse)
async def list_available_connectors(
    company_context: Annotated[CompanyContext, Depends(get_company_context)],
) -> AvailableConnectorsResponse:
    return AvailableConnectorsResponse(
        connectors=[
            ConnectorDefinitionResponse(
                provider=item.provider,
                name=item.name,
                group=item.group,
                description=item.description,
                credential_fields=[
                    CredentialFieldResponse(
                        key=field.key,
                        label=field.label,
                        secret=field.secret,
                        help_text=field.help_text,
                    )
                    for field in item.credential_fields
                ],
                capabilities=list(item.capabilities),
            )
            for item in CONNECTOR_REGISTRY
        ]
    )


@router.get("/connections", response_model=list[ConnectionResponse])
async def list_connections(
    company_context: Annotated[CompanyContext, Depends(get_company_context)],
    connection_repository: Annotated[ConnectionRepository, Depends(get_connection_repository)],
) -> list[ConnectionResponse]:
    connections = await connection_repository.list_all()
    return [_to_connection_response(connection) for connection in connections]


@router.post("/connect", response_model=ConnectionResponse, status_code=status.HTTP_201_CREATED)
async def connect(
    payload: ConnectRequest,
    company_context: Annotated[CompanyContext, Depends(require_role(*_MANAGEMENT_ROLES))],
    current_user: Annotated[User, Depends(get_current_user)],
    connection_repository: Annotated[ConnectionRepository, Depends(get_connection_repository)],
    cipher: Annotated[SecretCipher, Depends(get_secret_cipher)],
    connector_factory: Annotated[Callable[[str], Connector], Depends(get_connector_factory)],
    audit_repository: Annotated[AuditLogRepository, Depends(get_audit_log_repository)],
    subscription_repository: Annotated[
        SubscriptionRepository, Depends(get_subscription_repository)
    ],
) -> ConnectionResponse:
    # Só aplica o limite ao conectar um provedor novo; reconectar/atualizar
    # credenciais de um já existente não consome uma nova "vaga" de integração.
    existing = await connection_repository.get_by_provider(payload.provider)
    if existing is None:
        await ensure_can_add_integration(
            subscription_repository,
            connection_repository,
            company_id=company_context.company_id,
        )
    connector = connector_factory(payload.provider)
    use_case = ConnectProviderUseCase(connection_repository, cipher, connector)
    connection = await use_case.execute(provider=payload.provider, credentials=payload.credentials)
    await record_audit(
        audit_repository,
        "connector_connected",
        user_id=current_user.id,
        company_id=company_context.company_id,
        provider=payload.provider,
    )
    return _to_connection_response(connection)


@router.post("/{provider}/sync", response_model=SyncResultResponse)
async def sync(
    provider: str,
    company_context: Annotated[CompanyContext, Depends(require_role(*_MANAGEMENT_ROLES))],
    current_user: Annotated[User, Depends(get_current_user)],
    connection_repository: Annotated[ConnectionRepository, Depends(get_connection_repository)],
    category_repository: Annotated[
        FinancialCategoryRepository, Depends(get_financial_category_repository)
    ],
    transaction_repository: Annotated[
        FinancialTransactionRepository, Depends(get_financial_transaction_repository)
    ],
    cipher: Annotated[SecretCipher, Depends(get_secret_cipher)],
    connector_factory: Annotated[Callable[[str], Connector], Depends(get_connector_factory)],
    audit_repository: Annotated[AuditLogRepository, Depends(get_audit_log_repository)],
) -> SyncResultResponse:
    connector = connector_factory(provider)
    use_case = SyncConnectionUseCase(
        connection_repository,
        category_repository,
        transaction_repository,
        cipher,
        connector,
    )
    result = await use_case.execute(provider=provider, created_by=current_user.id)
    await record_audit(
        audit_repository,
        "connector_synced",
        user_id=current_user.id,
        company_id=company_context.company_id,
        provider=provider,
        imported=result.imported,
        skipped=result.skipped,
    )
    return SyncResultResponse(
        provider=provider,
        imported=result.imported,
        skipped=result.skipped,
        details=result.details,
    )


@router.delete("/{provider}", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect(
    provider: str,
    company_context: Annotated[CompanyContext, Depends(require_role(*_MANAGEMENT_ROLES))],
    current_user: Annotated[User, Depends(get_current_user)],
    connection_repository: Annotated[ConnectionRepository, Depends(get_connection_repository)],
    audit_repository: Annotated[AuditLogRepository, Depends(get_audit_log_repository)],
) -> None:
    deleted = await connection_repository.delete(provider)
    if not deleted:
        raise NotFoundError("Conexão não encontrada.")
    await record_audit(
        audit_repository,
        "connector_disconnected",
        user_id=current_user.id,
        company_id=company_context.company_id,
        provider=provider,
    )
