from dataclasses import dataclass
from datetime import datetime

from app.application.dashboard.get_dashboard import GetDashboardUseCase
from app.core.exceptions import NotFoundError, ValidationError
from app.domain.company.repository import CompanyRepository
from app.domain.dashboard.entities import DashboardSummary
from app.domain.insights.entities import FinancialInsight
from app.domain.insights.ports import InsightsAIPort


@dataclass
class InsightsResult:
    summary: DashboardSummary
    insights: list[FinancialInsight]


class GenerateFinancialInsightsUseCase:
    """Compõe o dashboard (agregados já validados/testados na Etapa 7) com a IA:
    os números são calculados pela aplicação e a IA apenas os interpreta — ela
    nunca calcula nem inventa valores."""

    def __init__(
        self,
        company_repository: CompanyRepository,
        dashboard_use_case: GetDashboardUseCase,
        insights_ai: InsightsAIPort,
    ) -> None:
        self._company_repository = company_repository
        self._dashboard_use_case = dashboard_use_case
        self._insights_ai = insights_ai

    async def execute(self, *, company_id: str, start: datetime, end: datetime) -> InsightsResult:
        company = await self._company_repository.get_by_id(company_id)
        if company is None:
            raise NotFoundError("Empresa não encontrada.")

        summary = await self._dashboard_use_case.execute(
            company_id=company_id, start=start, end=end
        )
        insights = await self._insights_ai.generate_financial_insights(
            company=company, summary=summary
        )
        return InsightsResult(summary=summary, insights=insights)


class SummarizePeriodUseCase:
    """Resumo executivo: a aplicação calcula, a IA narra."""

    def __init__(
        self,
        company_repository: CompanyRepository,
        dashboard_use_case: GetDashboardUseCase,
        insights_ai: InsightsAIPort,
    ) -> None:
        self._company_repository = company_repository
        self._dashboard_use_case = dashboard_use_case
        self._insights_ai = insights_ai

    async def execute(self, *, company_id: str, start: datetime, end: datetime) -> str:
        company = await self._company_repository.get_by_id(company_id)
        if company is None:
            raise NotFoundError("Empresa não encontrada.")
        summary = await self._dashboard_use_case.execute(
            company_id=company_id, start=start, end=end
        )
        return await self._insights_ai.generate_period_summary(company=company, summary=summary)


class AnswerFinancialQuestionUseCase:
    """Perguntas em linguagem natural respondidas apenas com os agregados do período."""

    def __init__(
        self,
        company_repository: CompanyRepository,
        dashboard_use_case: GetDashboardUseCase,
        insights_ai: InsightsAIPort,
    ) -> None:
        self._company_repository = company_repository
        self._dashboard_use_case = dashboard_use_case
        self._insights_ai = insights_ai

    async def execute(
        self, *, company_id: str, start: datetime, end: datetime, question: str
    ) -> str:
        normalized = question.strip()
        if len(normalized) < 3:
            raise ValidationError("Escreva uma pergunta um pouco mais completa.")
        company = await self._company_repository.get_by_id(company_id)
        if company is None:
            raise NotFoundError("Empresa não encontrada.")
        summary = await self._dashboard_use_case.execute(
            company_id=company_id, start=start, end=end
        )
        return await self._insights_ai.answer_financial_question(
            company=company, summary=summary, question=normalized
        )
