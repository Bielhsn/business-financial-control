"""Catálogo estático de planos de assinatura (Starter/Professional/Business/
Enterprise).

Este módulo é a fonte única da verdade para preços, limites e funcionalidades de
cada plano. Adicionar/ajustar um plano = editar o catálogo aqui; a API, o gating
e o frontend leem tudo daqui. Nenhum preço ou limite fica hard-coded em outro
lugar.
"""

from dataclasses import dataclass
from enum import StrEnum

# Sentinela para "ilimitado" em qualquer limite numérico.
UNLIMITED = -1


class PlanTier(StrEnum):
    STARTER = "starter"
    PROFESSIONAL = "professional"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"


class Feature(StrEnum):
    """Capacidades que podem ser liberadas/bloqueadas por plano. Usadas pelo
    gating para exibir "funcionalidades bloqueadas" e incentivar upgrade."""

    INTEGRATIONS = "integrations"  # conectar plataformas externas
    ADVANCED_AI = "advanced_ai"  # IA consultora, previsões e recomendações
    APPOINTMENTS = "appointments"  # módulo de agenda
    TEAM_MANAGEMENT = "team_management"  # convidar e gerenciar equipe
    ADVANCED_REPORTS = "advanced_reports"  # relatórios e exportações avançadas
    WHITE_LABEL = "white_label"  # branding próprio (logo/cores)
    API_ACCESS = "api_access"  # acesso à API pública
    PRIORITY_SUPPORT = "priority_support"  # suporte prioritário


@dataclass(frozen=True)
class PlanLimits:
    """Limites numéricos por empresa. UNLIMITED (-1) significa sem teto."""

    max_members: int
    max_integrations: int
    max_ai_insights_per_month: int
    max_catalog_items: int


@dataclass(frozen=True)
class PlanDefinition:
    tier: PlanTier
    name: str
    tagline: str
    target_audience: str
    price_cents_monthly: int  # em centavos de BRL (0 = grátis)
    price_cents_yearly: int  # cobrança anual (normalmente com desconto)
    limits: PlanLimits
    features: frozenset[Feature]
    highlights: tuple[str, ...]  # bullets de marketing para a página de preços
    is_contact_sales: bool = False  # Enterprise: "fale com vendas"
    badge: str | None = None  # ex.: "Mais popular"

    def has_feature(self, feature: Feature) -> bool:
        return feature in self.features


_ALL_FEATURES: frozenset[Feature] = frozenset(Feature)


PLAN_CATALOG: tuple[PlanDefinition, ...] = (
    PlanDefinition(
        tier=PlanTier.STARTER,
        name="Starter",
        tagline="Comece a organizar seu negócio sem custo.",
        target_audience="Autônomos e MEIs dando os primeiros passos.",
        price_cents_monthly=0,
        price_cents_yearly=0,
        limits=PlanLimits(
            max_members=2,
            max_integrations=1,
            max_ai_insights_per_month=10,
            max_catalog_items=50,
        ),
        features=frozenset({Feature.APPOINTMENTS, Feature.INTEGRATIONS}),
        highlights=(
            "Dashboard financeiro essencial",
            "Até 2 usuários",
            "1 integração conectada",
            "Agenda e catálogo básicos",
            "Insights de IA limitados (10/mês)",
        ),
    ),
    PlanDefinition(
        tier=PlanTier.PROFESSIONAL,
        name="Professional",
        tagline="Tudo que um pequeno negócio precisa para crescer.",
        target_audience="Pequenos negócios com equipe enxuta.",
        price_cents_monthly=4900,
        price_cents_yearly=49000,  # ~2 meses grátis no anual
        limits=PlanLimits(
            max_members=5,
            max_integrations=3,
            max_ai_insights_per_month=100,
            max_catalog_items=500,
        ),
        features=frozenset(
            {
                Feature.APPOINTMENTS,
                Feature.INTEGRATIONS,
                Feature.ADVANCED_AI,
                Feature.TEAM_MANAGEMENT,
            }
        ),
        badge="Mais popular",
        highlights=(
            "Tudo do Starter",
            "Até 5 usuários",
            "3 integrações (iFood, Shopify, Hotmart…)",
            "IA consultora com recomendações",
            "Gestão de equipe por papéis",
            "Insights de IA ampliados (100/mês)",
        ),
    ),
    PlanDefinition(
        tier=PlanTier.BUSINESS,
        name="Business",
        tagline="Escale com integrações, relatórios e branding próprio.",
        target_audience="Negócios em crescimento com múltiplos canais.",
        price_cents_monthly=14900,
        price_cents_yearly=149000,
        limits=PlanLimits(
            max_members=15,
            max_integrations=10,
            max_ai_insights_per_month=500,
            max_catalog_items=UNLIMITED,
        ),
        features=frozenset(
            {
                Feature.APPOINTMENTS,
                Feature.INTEGRATIONS,
                Feature.ADVANCED_AI,
                Feature.TEAM_MANAGEMENT,
                Feature.ADVANCED_REPORTS,
                Feature.WHITE_LABEL,
            }
        ),
        highlights=(
            "Tudo do Professional",
            "Até 15 usuários",
            "10 integrações conectadas",
            "Relatórios avançados e exportações",
            "White-label (logo e cores próprias)",
            "Catálogo ilimitado",
        ),
    ),
    PlanDefinition(
        tier=PlanTier.ENTERPRISE,
        name="Enterprise",
        tagline="Recursos ilimitados, API e suporte dedicado.",
        target_audience="Redes, franquias e operações de grande porte.",
        price_cents_monthly=49900,
        price_cents_yearly=499000,
        limits=PlanLimits(
            max_members=UNLIMITED,
            max_integrations=UNLIMITED,
            max_ai_insights_per_month=UNLIMITED,
            max_catalog_items=UNLIMITED,
        ),
        features=_ALL_FEATURES,
        is_contact_sales=True,
        highlights=(
            "Tudo do Business",
            "Usuários e integrações ilimitados",
            "Acesso à API pública",
            "Suporte prioritário dedicado",
            "IA sem limites de uso",
        ),
    ),
)

_BY_TIER: dict[PlanTier, PlanDefinition] = {plan.tier: plan for plan in PLAN_CATALOG}

# Plano padrão de uma empresa sem assinatura explícita.
DEFAULT_TIER = PlanTier.STARTER


def get_plan(tier: PlanTier) -> PlanDefinition:
    return _BY_TIER[tier]


def default_plan() -> PlanDefinition:
    return _BY_TIER[DEFAULT_TIER]
