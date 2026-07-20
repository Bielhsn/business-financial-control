from dataclasses import dataclass

from app.domain.connector.oauth import OAuthConfig


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
    # "credentials" = o usuário cola chaves (ex.: Hotmart); "oauth" = fluxo de
    # autorização por redirect (ex.: Shopify, Mercado Livre, iFood).
    auth_type: str = "credentials"
    oauth: OAuthConfig | None = None


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
    ConnectorDefinition(
        provider="mercadolivre",
        name="Mercado Livre",
        group="Marketplaces",
        description="Sincroniza pedidos e vendas do Mercado Livre com o financeiro.",
        credential_fields=(),
        capabilities=("sales", "orders", "refunds"),
        auth_type="oauth",
        oauth=OAuthConfig(
            authorize_url="https://auth.mercadolivre.com.br/authorization",
            token_url="https://api.mercadolibre.com/oauth/token",
            scopes=("offline_access", "read"),
            client_id_env="MERCADOLIVRE_CLIENT_ID",
            client_secret_env="MERCADOLIVRE_CLIENT_SECRET",
        ),
    ),
    ConnectorDefinition(
        provider="shopify",
        name="Shopify",
        group="E-commerce",
        description="Sincroniza pedidos e vendas da sua loja Shopify.",
        credential_fields=(),
        capabilities=("sales", "orders", "refunds"),
        auth_type="oauth",
        oauth=OAuthConfig(
            authorize_url="https://{shop}.myshopify.com/admin/oauth/authorize",
            token_url="https://{shop}.myshopify.com/admin/oauth/access_token",
            scopes=("read_orders", "read_products"),
            client_id_env="SHOPIFY_CLIENT_ID",
            client_secret_env="SHOPIFY_CLIENT_SECRET",
        ),
    ),
    ConnectorDefinition(
        provider="ifood",
        name="iFood",
        group="Delivery",
        description="Sincroniza pedidos, cancelamentos e repasses do iFood.",
        credential_fields=(),
        capabilities=("sales", "orders", "refunds", "cancellations"),
        auth_type="oauth",
        oauth=OAuthConfig(
            authorize_url="https://merchant-api.ifood.com.br/authentication/v1.0/oauth/authorize",
            token_url="https://merchant-api.ifood.com.br/authentication/v1.0/oauth/token",
            scopes=("merchant", "order"),
            client_id_env="IFOOD_CLIENT_ID",
            client_secret_env="IFOOD_CLIENT_SECRET",
        ),
    ),
)

CONNECTOR_PROVIDERS: frozenset[str] = frozenset(item.provider for item in CONNECTOR_REGISTRY)


def get_connector_definition(provider: str) -> ConnectorDefinition | None:
    return next((item for item in CONNECTOR_REGISTRY if item.provider == provider), None)
