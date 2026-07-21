from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.v1.deps import (
    get_api_key_repository,
    get_current_user,
    get_subscription_repository,
    require_role,
)
from app.application.apikey.manage import CreateApiKeyUseCase
from app.application.subscription.gating import ensure_feature
from app.core.config import Settings, get_settings
from app.core.exceptions import NotFoundError
from app.core.tenant import CompanyContext
from app.domain.apikey.entities import ApiKey, ApiKeyRepository
from app.domain.company.roles import CompanyRole
from app.domain.subscription.plans import Feature
from app.domain.subscription.repository import SubscriptionRepository
from app.domain.user.entities import User
from app.schemas.api_key import (
    ApiKeyResponse,
    CreateApiKeyRequest,
    CreatedApiKeyResponse,
)

router = APIRouter(prefix="/companies/{company_id}/api-keys", tags=["api-keys"])

_OWNER_ADMIN = (CompanyRole.OWNER, CompanyRole.ADMIN)


def _to_response(key: ApiKey) -> ApiKeyResponse:
    return ApiKeyResponse(
        id=key.id,
        name=key.name,
        prefix=key.prefix,
        created_at=key.created_at,
        last_used_at=key.last_used_at,
        revoked=key.revoked,
    )


@router.get("", response_model=list[ApiKeyResponse])
async def list_api_keys(
    company_context: Annotated[CompanyContext, Depends(require_role(*_OWNER_ADMIN))],
    api_key_repository: Annotated[ApiKeyRepository, Depends(get_api_key_repository)],
) -> list[ApiKeyResponse]:
    keys = await api_key_repository.list_for_company()
    return [_to_response(key) for key in keys]


@router.post("", response_model=CreatedApiKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    payload: CreateApiKeyRequest,
    company_context: Annotated[CompanyContext, Depends(require_role(*_OWNER_ADMIN))],
    current_user: Annotated[User, Depends(get_current_user)],
    api_key_repository: Annotated[ApiKeyRepository, Depends(get_api_key_repository)],
    subscription_repository: Annotated[
        SubscriptionRepository, Depends(get_subscription_repository)
    ],
    settings: Annotated[Settings, Depends(get_settings)],
) -> CreatedApiKeyResponse:
    # Recurso exclusivo de planos com acesso à API (ex.: Enterprise).
    await ensure_feature(
        subscription_repository,
        company_id=company_context.company_id,
        feature=Feature.API_ACCESS,
    )
    created = await CreateApiKeyUseCase(api_key_repository, secret=settings.secret_key).execute(
        name=payload.name
    )
    key = created.api_key
    return CreatedApiKeyResponse(
        id=key.id,
        name=key.name,
        prefix=key.prefix,
        created_at=key.created_at,
        last_used_at=key.last_used_at,
        revoked=key.revoked,
        raw_key=created.raw_key,
    )


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: str,
    company_context: Annotated[CompanyContext, Depends(require_role(*_OWNER_ADMIN))],
    api_key_repository: Annotated[ApiKeyRepository, Depends(get_api_key_repository)],
) -> None:
    revoked = await api_key_repository.revoke(key_id)
    if not revoked:
        raise NotFoundError("Chave de API não encontrada.")
