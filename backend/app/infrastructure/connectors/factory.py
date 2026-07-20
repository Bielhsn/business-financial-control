from app.core.exceptions import ValidationError
from app.domain.connector.ports import Connector
from app.infrastructure.connectors.hotmart import HotmartConnector

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
