from dataclasses import dataclass


@dataclass(frozen=True)
class CredentialField:
    """Um campo de credencial que o provedor exige, usado pela API e pelo
    frontend para renderizar o formulário de conexão dinamicamente."""

    key: str
    label: str
    secret: bool = True
    help_text: str | None = None


@dataclass(frozen=True)
class ConnectorDefinition:
    provider: str
    name: str
    group: str
    description: str
    credential_fields: tuple[CredentialField, ...]
    capabilities: tuple[str, ...]


# Catálogo dos provedores integráveis. Adicionar um conector = adicionar uma
# linha aqui + a classe no factory. Nenhuma outra parte do sistema muda.
CONNECTOR_REGISTRY: tuple[ConnectorDefinition, ...] = (
    ConnectorDefinition(
        provider="hotmart",
        name="Hotmart",
        group="Infoprodutos",
        description="Sincroniza vendas e reembolsos da Hotmart com o financeiro.",
        credential_fields=(
            CredentialField(
                "client_id",
                "Client ID",
                secret=False,
                help_text="Hotmart → Ferramentas → Credenciais Hotmart API.",
            ),
            CredentialField("client_secret", "Client Secret", secret=True),
        ),
        capabilities=("sales", "refunds"),
    ),
)

CONNECTOR_PROVIDERS: frozenset[str] = frozenset(item.provider for item in CONNECTOR_REGISTRY)


def get_connector_definition(provider: str) -> ConnectorDefinition | None:
    return next((item for item in CONNECTOR_REGISTRY if item.provider == provider), None)
