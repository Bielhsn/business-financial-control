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
    # Nem todo provedor entrega o par completo: alguns dão só uma chave de API,
    # outros dispensam o segredo. Pedir um campo que não existe do outro lado
    # trava a conexão sem motivo, então cada provedor declara o que é essencial.
    # O padrão é obrigatório — dispensar é a exceção, e precisa ser explícita.
    required: bool = True


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
    # O iFood NÃO usa authorization-code por redirect: não existe endpoint
    # `/oauth/authorize` (o gateway responde "no Route matched with those
    # values"). São dois modelos:
    #   - centralizado: o lojista registra o próprio aplicativo e usa
    #     client_credentials para acessar as lojas dele — é o que está aqui;
    #   - distribuído: o integrador atende lojas de terceiros e a autorização
    #     acontece por `userCode` (o lojista digita um código no portal do
    #     iFood), o que exige homologação do app como distribuidor.
    # Por isso o iFood entra como "credentials" (o lojista cola as chaves do
    # aplicativo dele), e não pelo fluxo genérico de OAuth por redirect.
    ConnectorDefinition(
        provider="ifood",
        name="iFood",
        group="Delivery",
        description="Sincroniza pedidos, cancelamentos e repasses do iFood.",
        credential_fields=(
            CredentialField(
                "client_id",
                "Client ID",
                secret=False,
                help_text=(
                    "Portal do Desenvolvedor iFood → seu aplicativo → Credenciais. É um UUID."
                ),
            ),
            # Continua obrigatório: a API do iFood responde "Client secret is
            # mandatory" quando o campo não vai no corpo. O segredo é exibido
            # uma única vez, no momento em que a credencial é gerada — quem não
            # o encontra no portal precisa gerar a credencial de novo, não
            # conectar sem ele.
            CredentialField(
                "client_secret",
                "Client Secret",
                secret=True,
                help_text=(
                    "Aparece uma única vez, quando a credencial é gerada no portal. "
                    "Se não estiver visível, gere uma nova credencial do aplicativo."
                ),
            ),
        ),
        capabilities=("sales", "orders", "refunds", "cancellations"),
    ),
)

CONNECTOR_PROVIDERS: frozenset[str] = frozenset(item.provider for item in CONNECTOR_REGISTRY)


def get_connector_definition(provider: str) -> ConnectorDefinition | None:
    return next((item for item in CONNECTOR_REGISTRY if item.provider == provider), None)
