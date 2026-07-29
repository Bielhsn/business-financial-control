import httpx

from app.core.config import Settings, get_settings
from app.core.exceptions import AIProviderNotConfiguredError, ValidationError
from app.domain.connector.oauth import OAuthProvider
from app.domain.connector.ports import Connector
from app.domain.connector.registry import get_connector_definition
from app.infrastructure.connectors.hotmart import HotmartConnector
from app.infrastructure.connectors.ifood import IFoodConnector
from app.infrastructure.connectors.oauth_base import GenericOAuth2Connector

# Mapa provedor → construtor do conector. Adicionar um provedor = uma linha aqui
# (mais a definição no CONNECTOR_REGISTRY). O restante do sistema não muda.
#
# Conectores OAuth (ex.: iFood) autorizam a loja pelo fluxo genérico de OAuth e
# leem as vendas com o token guardado — por isso aparecem aqui (para o motor de
# sync) além do registro OAuth no CONNECTOR_REGISTRY.
_BUILDERS: dict[str, type[Connector]] = {
    "hotmart": HotmartConnector,
    "ifood": IFoodConnector,
}


def build_connector(provider: str, settings: Settings | None = None) -> Connector:
    builder = _BUILDERS.get(provider)
    if builder is None:
        raise ValidationError(f"Provedor de integração '{provider}' não é suportado.")

    # O iFood autentica com as chaves do aplicativo da PLATAFORMA (ver o módulo
    # do conector): elas vêm do ambiente do servidor, não das credenciais que o
    # lojista digitou. Os demais conectores usam só o que o lojista informou.
    if provider == "ifood":
        resolved = settings or get_settings()
        return IFoodConnector(
            client_id=resolved.ifood_client_id,
            client_secret=resolved.ifood_client_secret,
        )
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
