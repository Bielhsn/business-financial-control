from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.v1.deps import (
    get_ai_provider,
    get_company_blueprint_repository,
    get_company_repository,
    get_financial_category_repository,
    get_financial_transaction_repository,
    require_role,
)
from app.application.dashboard.get_dashboard import GetDashboardUseCase
from app.application.insights.generate_insights import GenerateFinancialInsightsUseCase
from app.core.tenant import CompanyContext
from app.domain.blueprint.repository import CompanyBlueprintRepository
from app.domain.company.repository import CompanyRepository
from app.domain.company.roles import CompanyRole
from app.domain.financial.repository import (
    FinancialCategoryRepository,
    FinancialTransactionRepository,
)
from app.domain.insights.ports import InsightsAIPort
from app.schemas.insights import GenerateInsightsRequest, InsightResponse, InsightsResponse

router = APIRouter(prefix="/companies/{company_id}/insights", tags=["insights"])


# POST (não GET): a geração consome tokens do provedor de IA — não deve ser disparada
# por prefetch/refetch automático de clientes HTTP. Restrita a papéis de gestão.
@router.post("", response_model=InsightsResponse)
async def generate_insights(
    payload: GenerateInsightsRequest,
    company_context: Annotated[
        CompanyContext,
        Depends(require_role(CompanyRole.OWNER, CompanyRole.ADMIN, CompanyRole.MANAGER)),
    ],
    company_repository: Annotated[CompanyRepository, Depends(get_company_repository)],
    transaction_repository: Annotated[
        FinancialTransactionRepository, Depends(get_financial_transaction_repository)
    ],
    category_repository: Annotated[
        FinancialCategoryRepository, Depends(get_financial_category_repository)
    ],
    blueprint_repository: Annotated[
        CompanyBlueprintRepository, Depends(get_company_blueprint_repository)
    ],
    ai_provider: Annotated[InsightsAIPort, Depends(get_ai_provider)],
) -> InsightsResponse:
    dashboard_use_case = GetDashboardUseCase(
        transaction_repository, category_repository, blueprint_repository
    )
    use_case = GenerateFinancialInsightsUseCase(company_repository, dashboard_use_case, ai_provider)
    result = await use_case.execute(
        company_id=company_context.company_id, start=payload.start, end=payload.end
    )
    return InsightsResponse(
        start=result.summary.start,
        end=result.summary.end,
        insights=[
            InsightResponse(kind=item.kind, title=item.title, message=item.message)
            for item in result.insights
        ],
    )
