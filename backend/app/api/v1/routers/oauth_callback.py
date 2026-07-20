from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse

from app.api.v1.deps import get_connection_repository, get_secret_cipher
from app.application.connector.oauth_flow import CompleteOAuthUseCase, oauth_redirect_uri
from app.core.config import Settings, get_settings
from app.core.exceptions import AppError
from app.core.logging import get_logger
from app.core.tenant import set_current_company_id
from app.domain.connector.oauth import parse_oauth_state
from app.domain.connector.ports import SecretCipher
from app.domain.connector.repository import ConnectionRepository
from app.infrastructure.connectors.factory import build_oauth_provider

logger = get_logger(__name__)

# Fora do escopo /companies/{id}: o provedor redireciona o navegador para cá e o
# contexto da empresa vem do `state` assinado (que também funciona como CSRF).
router = APIRouter(prefix="/connectors", tags=["connectors"])


def _frontend_base(settings: Settings) -> str:
    origins = settings.cors_origins
    return origins[0] if origins else "/"


@router.get("/oauth/callback")
async def oauth_callback(
    connection_repository: Annotated[ConnectionRepository, Depends(get_connection_repository)],
    cipher: Annotated[SecretCipher, Depends(get_secret_cipher)],
    settings: Annotated[Settings, Depends(get_settings)],
    code: Annotated[str | None, Query()] = None,
    state: Annotated[str | None, Query()] = None,
    error: Annotated[str | None, Query()] = None,
) -> RedirectResponse:
    frontend = _frontend_base(settings).rstrip("/")

    if error is not None or code is None or state is None:
        return RedirectResponse(url=f"{frontend}/companies?integration_error=1")

    try:
        payload = parse_oauth_state(state, secret_key=settings.secret_key)
        set_current_company_id(payload.company_id)
        provider_obj = build_oauth_provider(
            payload.provider, settings, url_params=payload.params or None
        )
        use_case = CompleteOAuthUseCase(connection_repository, cipher)
        await use_case.execute(
            provider_obj,
            provider=payload.provider,
            code=code,
            redirect_uri=oauth_redirect_uri(settings.public_base_url),
            config=payload.params,
        )
    except AppError as exc:
        logger.warning("oauth_callback_failed", error=exc.message)
        return RedirectResponse(url=f"{frontend}/companies?integration_error=1")

    return RedirectResponse(
        url=f"{frontend}/c/{payload.company_id}/integrations?connected={payload.provider}"
    )
