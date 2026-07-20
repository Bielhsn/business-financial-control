import httpx

from app.core.config import Settings
from app.core.exceptions import AIProviderNotConfiguredError, ValidationError
from app.domain.connector.oauth import OAuthProvider
from app.domain.connector.ports import Connector
from app.domain.connector.registry import get_connector_definition
from app.infrastructure.connectors.hotmart import HotmartConnector
from app.infrastructure.connectors.oauth_base import GenericOAuth2Connector

# Mapa provedor → construtor do conector. Adicionar um provedor = uma linha aqui
# (mais a definição no CONNECTOR_REGISTRY). O restante do sistema não muda.
_BUILDERS: dict[str, type[Connector]] = {
    "hotmart": HotmartConnector,
}


def build_connector(provider: str) -> Connector:
    builder = _BUILDERS.get(provider)
    if builder is None:
        raise ValidationError(f"Provedor de integração '{provider}' não é suportado.")
    return builder()


def build_oauth_provider(
    provider: str,
    settings: Settings,
    *,
    url_params: dict[str, str] | None = None,
    transport: httpx.AsyncBaseTransport | None = None,
) -> OAuthProvider:
    """Constrói o conector OAuth de um provedor a partir do registro + credenciais
    do app parceiro (env). Um novo provedor OAuth não precisa de código novo aqui."""
    definition = get_connector_definition(provider)
    if definition is None or definition.auth_type != "oauth" or definition.oauth is None:
        raise ValidationError(f"Provedor '{provider}' não usa OAuth.")

    credentials = settings.oauth_client_credentials(
        definition.oauth.client_id_env, definition.oauth.client_secret_env
    )
    if credentials is None:
        raise AIProviderNotConfiguredError(
            f"Integração {definition.name} indisponível: configure "
            f"{definition.oauth.client_id_env} e {definition.oauth.client_secret_env}."
        )
    client_id, client_secret = credentials
    return GenericOAuth2Connector(
        provider=provider,
        config=definition.oauth,
        client_id=client_id,
        client_secret=client_secret,
        url_params=url_params,
        transport=transport,
    )
