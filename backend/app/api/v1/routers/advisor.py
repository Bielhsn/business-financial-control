from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.v1.deps import (
    get_ai_provider,
    get_audit_log_repository,
    get_catalog_item_repository,
    get_company_blueprint_repository,
    get_company_repository,
    get_financial_category_repository,
    get_financial_transaction_repository,
    require_role,
)
from app.application.advisor.compute_signals import ComputeBusinessSignalsUseCase
from app.application.advisor.recommend import GenerateAdvisorRecommendationsUseCase
from app.application.dashboard.get_dashboard import GetDashboardUseCase
from app.core.audit import record_audit
from app.core.tenant import CompanyContext
from app.domain.advisor.entities import BusinessSignal
from app.domain.audit.repository import AuditLogRepository
from app.domain.blueprint.repository import CompanyBlueprintRepository
from app.domain.catalog.repository import CatalogItemRepository
from app.domain.company.repository import CompanyRepository
from app.domain.company.roles import CompanyRole
from app.domain.financial.repository import (
    FinancialCategoryRepository,
    FinancialTransactionRepository,
)
from app.domain.insights.ports import InsightsAIPort
from app.schemas.advisor import (
    BusinessSignalResponse,
    RecommendationsResponse,
    SignalsResponse,
)

router = APIRouter(prefix="/companies/{company_id}/advisor", tags=["advisor"])

_MANAGEMENT_ROLES = (CompanyRole.OWNER, CompanyRole.ADMIN, CompanyRole.MANAGER)


def _to_signal_response(signal: BusinessSignal) -> BusinessSignalResponse:
    return BusinessSignalResponse(
        kind=signal.kind,
        severity=signal.severity,
        title=signal.title,
        detail=signal.detail,
    )


# GET: os sinais são 100% computados pela aplicação (sem IA) — baratos e sem
# efeitos colaterais, podem ser recarregados à vontade pelo frontend.
@router.get("/signals", response_model=SignalsResponse)
async def list_signals(
    company_context: Annotated[CompanyContext, Depends(require_role(*_MANAGEMENT_ROLES))],
    item_repository: Annotated[CatalogItemRepository, Depends(get_catalog_item_repository)],
    transaction_repository: Annotated[
        FinancialTransactionRepository, Depends(get_financial_transaction_repository)
    ],
    category_repository: Annotated[
        FinancialCategoryRepository, Depends(get_financial_category_repository)
    ],
    blueprint_repository: Annotated[
        CompanyBlueprintRepository, Depends(get_company_blueprint_repository)
    ],
) -> SignalsResponse:
    dashboard_use_case = GetDashboardUseCase(
        transaction_repository, category_repository, blueprint_repository
    )
    use_case = ComputeBusinessSignalsUseCase(
        item_repository, transaction_repository, dashboard_use_case
    )
    signals = await use_case.execute(company_id=company_context.company_id)
    return SignalsResponse(signals=[_to_signal_response(signal) for signal in signals])


# POST (não GET): a narração das recomendações consome tokens do provedor de IA.
@router.post("/recommendations", response_model=RecommendationsResponse)
async def generate_recommendations(
    company_context: Annotated[CompanyContext, Depends(require_role(*_MANAGEMENT_ROLES))],
    company_repository: Annotated[CompanyRepository, Depends(get_company_repository)],
    item_repository: Annotated[CatalogItemRepository, Depends(get_catalog_item_repository)],
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
    audit_repository: Annotated[AuditLogRepository, Depends(get_audit_log_repository)],
) -> RecommendationsResponse:
    dashboard_use_case = GetDashboardUseCase(
        transaction_repository, category_repository, blueprint_repository
    )
    signals_use_case = ComputeBusinessSignalsUseCase(
        item_repository, transaction_repository, dashboard_use_case
    )
    use_case = GenerateAdvisorRecommendationsUseCase(
        company_repository, signals_use_case, dashboard_use_case, ai_provider
    )
    result = await use_case.execute(company_id=company_context.company_id)
    await record_audit(
        audit_repository,
        "advisor_recommendations_generated",
        company_id=company_context.company_id,
        signal_count=len(result.signals),
    )
    return RecommendationsResponse(
        signals=[_to_signal_response(signal) for signal in result.signals],
        recommendations=result.recommendations,
    )
