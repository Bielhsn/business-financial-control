from dataclasses import dataclass


@dataclass(frozen=True)
class IntegrationDefinition:
    id: str
    name: str
    group: str

    @property
    def is_connectable(self) -> bool:
        """True quando existe conector implementado — ou seja, quando o botão
        "Conectar" leva a um fluxo real. O resto do catálogo mostra que a
        plataforma é suportada pelo produto, sem prometer conexão que não existe.

        Import local evita ciclo: o registro de conectores é infraestrutura.
        """
        from app.domain.connector.registry import CONNECTOR_PROVIDERS

        # O id do catálogo e o provider do conector divergem em um caso histórico.
        provider = "mercadolivre" if self.id == "mercado_livre" else self.id
        return provider in CONNECTOR_PROVIDERS


# Catálogo fechado de integrações que a plataforma conhece. A IA seleciona as
# relevantes para o segmento da empresa no blueprint (mesmo padrão de enum
# controlado dos módulos e das métricas de KPI) — nunca inventa conectores.
# Adicionar um conector novo = adicionar uma linha aqui (e o adapter, quando
# a integração real for construída).
INTEGRATION_REGISTRY: tuple[IntegrationDefinition, ...] = (
    # Delivery e food service
    IntegrationDefinition("ifood", "iFood", "Delivery"),
    IntegrationDefinition("rappi", "Rappi", "Delivery"),
    IntegrationDefinition("uber_eats", "Uber Eats", "Delivery"),
    IntegrationDefinition("anota_ai", "Anota AI", "Delivery"),
    IntegrationDefinition("goomer", "Goomer", "Delivery"),
    IntegrationDefinition("kds", "Sistema de cozinha (KDS)", "Restaurantes"),
    # Infoprodutos e cursos online (a Hotmart já tem conector implementado, mas
    # estava fora do catálogo — quem vende curso não a via na lista).
    IntegrationDefinition("hotmart", "Hotmart", "Infoprodutos"),
    IntegrationDefinition("kiwify", "Kiwify", "Infoprodutos"),
    IntegrationDefinition("eduzz", "Eduzz", "Infoprodutos"),
    IntegrationDefinition("monetizze", "Monetizze", "Infoprodutos"),
    # E-commerce
    IntegrationDefinition("shopify", "Shopify", "E-commerce"),
    IntegrationDefinition("nuvemshop", "Nuvemshop", "E-commerce"),
    IntegrationDefinition("tray", "Tray", "E-commerce"),
    IntegrationDefinition("loja_integrada", "Loja Integrada", "E-commerce"),
    IntegrationDefinition("woocommerce", "WooCommerce", "E-commerce"),
    # Marketplaces e social commerce
    IntegrationDefinition("mercado_livre", "Mercado Livre", "Marketplaces"),
    IntegrationDefinition("amazon", "Amazon", "Marketplaces"),
    IntegrationDefinition("shopee", "Shopee", "Marketplaces"),
    IntegrationDefinition("magalu", "Magalu", "Marketplaces"),
    IntegrationDefinition("tiktok_shop", "TikTok Shop", "Social commerce"),
    IntegrationDefinition("meta_commerce", "Meta Commerce (Instagram/Facebook)", "Social commerce"),
    IntegrationDefinition("google_merchant", "Google Merchant Center", "Social commerce"),
    # Logística
    IntegrationDefinition("melhor_envio", "Melhor Envio", "Logística"),
    IntegrationDefinition("correios", "Correios", "Logística"),
    IntegrationDefinition("jadlog", "Jadlog", "Logística"),
    IntegrationDefinition("loggi", "Loggi", "Logística"),
    # Pagamentos
    IntegrationDefinition("mercado_pago", "Mercado Pago", "Pagamentos"),
    IntegrationDefinition("stripe", "Stripe", "Pagamentos"),
    IntegrationDefinition("pagseguro", "PagSeguro", "Pagamentos"),
    IntegrationDefinition("asaas", "Asaas", "Pagamentos"),
    IntegrationDefinition("pagarme", "Pagar.me", "Pagamentos"),
    IntegrationDefinition("pix", "Pix", "Pagamentos"),
    IntegrationDefinition("maquininhas", "Maquininhas de cartão", "Pagamentos"),
    IntegrationDefinition("pagamentos_recorrentes", "Pagamentos recorrentes", "Pagamentos"),
    # Bancos
    IntegrationDefinition("nubank_pj", "Nubank PJ", "Bancos"),
    IntegrationDefinition("inter", "Inter Empresas", "Bancos"),
    IntegrationDefinition("itau", "Itaú", "Bancos"),
    IntegrationDefinition("c6", "C6 Bank", "Bancos"),
    # ERP, fiscal e contabilidade
    IntegrationDefinition("omie", "Omie", "Contabilidade e fiscal"),
    IntegrationDefinition("conta_azul", "Conta Azul", "Contabilidade e fiscal"),
    IntegrationDefinition("bling", "Bling", "Contabilidade e fiscal"),
    IntegrationDefinition("nota_fiscal", "Emissão de Nota Fiscal", "Contabilidade e fiscal"),
    # Agendamento
    IntegrationDefinition("google_agenda", "Google Agenda", "Agendamento"),
    IntegrationDefinition("calendly", "Calendly", "Agendamento"),
    # Fitness e saúde
    IntegrationDefinition("gympass", "Wellhub (Gympass)", "Fitness"),
    IntegrationDefinition("totalpass", "TotalPass", "Fitness"),
    IntegrationDefinition("catraca", "Controle de acesso (catraca)", "Fitness"),
    IntegrationDefinition("convenios", "Convênios de saúde", "Saúde"),
    # CRM e marketing
    IntegrationDefinition("hubspot", "HubSpot", "CRM e marketing"),
    IntegrationDefinition("pipedrive", "Pipedrive", "CRM e marketing"),
    IntegrationDefinition("rd_station", "RD Station", "CRM e marketing"),
    IntegrationDefinition("salesforce", "Salesforce", "CRM e marketing"),
    IntegrationDefinition("email_marketing", "E-mail marketing", "CRM e marketing"),
    IntegrationDefinition("programa_fidelidade", "Programa de fidelidade", "CRM e marketing"),
    # Comunicação
    IntegrationDefinition("whatsapp", "WhatsApp Business", "Comunicação"),
    IntegrationDefinition("slack", "Slack", "Comunicação"),
    IntegrationDefinition("discord", "Discord", "Comunicação"),
    IntegrationDefinition("instagram", "Instagram", "Comunicação"),
    # Analytics e produto (tech/SaaS)
    IntegrationDefinition("google_analytics", "Google Analytics", "Analytics e produto"),
    IntegrationDefinition("mixpanel", "Mixpanel", "Analytics e produto"),
    IntegrationDefinition("posthog", "PostHog", "Analytics e produto"),
    IntegrationDefinition("sentry", "Sentry", "Analytics e produto"),
    IntegrationDefinition("github", "GitHub", "Analytics e produto"),
)

INTEGRATION_IDS: frozenset[str] = frozenset(item.id for item in INTEGRATION_REGISTRY)


def get_integration(integration_id: str) -> IntegrationDefinition | None:
    return next((item for item in INTEGRATION_REGISTRY if item.id == integration_id), None)
