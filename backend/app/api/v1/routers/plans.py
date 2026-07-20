from fastapi import APIRouter

from app.domain.subscription.plans import PLAN_CATALOG, PlanDefinition
from app.schemas.subscription import PlanCatalogResponse, PlanLimitsResponse, PlanResponse

router = APIRouter(prefix="/plans", tags=["plans"])


def to_plan_response(plan: PlanDefinition) -> PlanResponse:
    return PlanResponse(
        tier=plan.tier,
        name=plan.name,
        tagline=plan.tagline,
        target_audience=plan.target_audience,
        price_cents_monthly=plan.price_cents_monthly,
        price_cents_yearly=plan.price_cents_yearly,
        limits=PlanLimitsResponse(
            max_members=plan.limits.max_members,
            max_integrations=plan.limits.max_integrations,
            max_ai_insights_per_month=plan.limits.max_ai_insights_per_month,
            max_catalog_items=plan.limits.max_catalog_items,
        ),
        features=[feature.value for feature in plan.features],
        highlights=list(plan.highlights),
        is_contact_sales=plan.is_contact_sales,
        badge=plan.badge,
    )


@router.get("", response_model=PlanCatalogResponse)
async def list_plans() -> PlanCatalogResponse:
    """Catálogo público de planos — alimenta a página de preços (pré-login)."""
    return PlanCatalogResponse(plans=[to_plan_response(plan) for plan in PLAN_CATALOG])
