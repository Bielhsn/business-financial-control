from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.v1.deps import (
    get_client_repository,
    get_company_blueprint_repository,
    get_company_context,
    get_financial_transaction_repository,
    require_role,
)
from app.application.client.create_client import CreateClientUseCase
from app.application.client.get_client_summary import GetClientSummaryUseCase
from app.application.client.update_client import UpdateClientUseCase
from app.core.exceptions import NotFoundError
from app.core.tenant import CompanyContext
from app.domain.blueprint.repository import CompanyBlueprintRepository
from app.domain.client.entities import Client, ClientSummary
from app.domain.client.repository import ClientRepository
from app.domain.company.roles import CompanyRole
from app.domain.financial.repository import FinancialTransactionRepository
from app.schemas.client import (
    ClientResponse,
    ClientSummaryResponse,
    CreateClientRequest,
    UpdateClientRequest,
)

router = APIRouter(prefix="/companies/{company_id}/clients", tags=["clients"])

_STAFF_ROLES = (
    CompanyRole.OWNER,
    CompanyRole.ADMIN,
    CompanyRole.MANAGER,
    CompanyRole.EMPLOYEE,
)


def _to_response(client: Client) -> ClientResponse:
    return ClientResponse(
        id=client.id,
        company_id=client.company_id,
        name=client.name,
        email=client.email,
        phone=client.phone,
        notes=client.notes,
        custom_fields=client.custom_fields,
        is_active=client.is_active,
        created_at=client.created_at,
        updated_at=client.updated_at,
    )


def _summary_to_response(summary: ClientSummary) -> ClientSummaryResponse:
    return ClientSummaryResponse(
        client_id=summary.client_id,
        total_spent_cents=summary.total_spent_cents,
        purchase_count=summary.purchase_count,
        last_purchase_at=summary.last_purchase_at,
    )


@router.post("", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(
    payload: CreateClientRequest,
    company_context: Annotated[CompanyContext, Depends(require_role(*_STAFF_ROLES))],
    client_repository: Annotated[ClientRepository, Depends(get_client_repository)],
    blueprint_repository: Annotated[
        CompanyBlueprintRepository, Depends(get_company_blueprint_repository)
    ],
) -> ClientResponse:
    use_case = CreateClientUseCase(client_repository, blueprint_repository)
    client = await use_case.execute(
        company_id=company_context.company_id,
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        notes=payload.notes,
        custom_fields=payload.custom_fields,
    )
    return _to_response(client)


@router.get("", response_model=list[ClientResponse])
async def list_clients(
    company_context: Annotated[CompanyContext, Depends(get_company_context)],
    client_repository: Annotated[ClientRepository, Depends(get_client_repository)],
    only_active: Annotated[bool, Query()] = True,
) -> list[ClientResponse]:
    clients = await client_repository.list_all(only_active=only_active)
    return [_to_response(client) for client in clients]


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: str,
    company_context: Annotated[CompanyContext, Depends(get_company_context)],
    client_repository: Annotated[ClientRepository, Depends(get_client_repository)],
) -> ClientResponse:
    client = await client_repository.get_by_id(client_id)
    if client is None:
        raise NotFoundError("Cliente não encontrado.")
    return _to_response(client)


@router.patch("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: str,
    payload: UpdateClientRequest,
    company_context: Annotated[CompanyContext, Depends(require_role(*_STAFF_ROLES))],
    client_repository: Annotated[ClientRepository, Depends(get_client_repository)],
    blueprint_repository: Annotated[
        CompanyBlueprintRepository, Depends(get_company_blueprint_repository)
    ],
) -> ClientResponse:
    use_case = UpdateClientUseCase(client_repository, blueprint_repository)
    client = await use_case.execute(
        company_id=company_context.company_id,
        client_id=client_id,
        **payload.model_dump(exclude_unset=True),
    )
    return _to_response(client)


@router.get("/{client_id}/summary", response_model=ClientSummaryResponse)
async def get_client_summary(
    client_id: str,
    company_context: Annotated[CompanyContext, Depends(get_company_context)],
    client_repository: Annotated[ClientRepository, Depends(get_client_repository)],
    transaction_repository: Annotated[
        FinancialTransactionRepository, Depends(get_financial_transaction_repository)
    ],
) -> ClientSummaryResponse:
    use_case = GetClientSummaryUseCase(client_repository, transaction_repository)
    summary = await use_case.execute(client_id=client_id)
    return _summary_to_response(summary)
