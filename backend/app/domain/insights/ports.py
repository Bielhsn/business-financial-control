from typing import Protocol

from app.domain.company.entities import Company
from app.domain.dashboard.entities import DashboardSummary
from app.domain.insights.entities import FinancialInsight


class InsightsAIPort(Protocol):
    """Gera insights financeiros a partir dos agregados já computados do dashboard.

    Recebe apenas agregados (nunca lançamentos individuais): menos tokens, resposta
    mais focada e nenhum dado granular de clientes trafega para o provedor de IA.
    """

    async def generate_financial_insights(
        self, *, company: Company, summary: DashboardSummary
    ) -> list[FinancialInsight]: ...
