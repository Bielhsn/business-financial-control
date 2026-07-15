from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.application.advisor.compute_signals import ComputeBusinessSignalsUseCase
from app.application.dashboard.get_dashboard import GetDashboardUseCase
from app.core.exceptions import NotFoundError
from app.domain.advisor.entities import BusinessSignal
from app.domain.company.repository import CompanyRepository
from app.domain.insights.ports import InsightsAIPort


@dataclass
class AdvisorRecommendations:
    signals: list[BusinessSignal]
    recommendations: str


class GenerateAdvisorRecommendationsUseCase:
    """A aplicação computa os sinais; a IA apenas prioriza e narra o plano de ação."""

    def __init__(
        self,
        company_repository: CompanyRepository,
        signals_use_case: ComputeBusinessSignalsUseCase,
        dashboard_use_case: GetDashboardUseCase,
        insights_ai: InsightsAIPort,
    ) -> None:
        self._company_repository = company_repository
        self._signals_use_case = signals_use_case
        self._dashboard_use_case = dashboard_use_case
        self._insights_ai = insights_ai

    async def execute(self, *, company_id: str) -> AdvisorRecommendations:
        company = await self._company_repository.get_by_id(company_id)
        if company is None:
            raise NotFoundError("Empresa não encontrada.")

        signals = await self._signals_use_case.execute(company_id=company_id)
        now = datetime.now(UTC)
        summary = await self._dashboard_use_case.execute(
            company_id=company_id, start=now - timedelta(days=90), end=now
        )
        recommendations = await self._insights_ai.generate_recommendations(
            company=company, summary=summary, signals=signals
        )
        return AdvisorRecommendations(signals=signals, recommendations=recommendations)
