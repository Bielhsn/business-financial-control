from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.v1.deps import (
    get_ai_provider,
    get_company_blueprint_repository,
    get_company_context,
    get_company_repository,
    require_role,
)
from app.application.blueprint.generate_blueprint import GenerateCompanyBlueprintUseCase
from app.application.blueprint.get_blueprint import GetCompanyBlueprintUseCase
from app.core.config import Settings, get_settings
from app.core.tenant import CompanyContext
from app.domain.blueprint.entities import CompanyBlueprint
from app.domain.blueprint.ports import AIProviderPort
from app.domain.blueprint.repository import CompanyBlueprintRepository
from app.domain.company.repository import CompanyRepository
from app.domain.company.roles import CompanyRole
from app.schemas.blueprint import (
    CompanyBlueprintResponse,
    CustomFieldResponse,
    FinancialCategoryResponse,
    GenerateBlueprintRequest,
    KPIResponse,
)

router = APIRouter(prefix="/companies/{company_id}/blueprint", tags=["blueprint"])


def _to_response(blueprint: CompanyBlueprint) -> CompanyBlueprintResponse:
    return CompanyBlueprintResponse(
        id=blueprint.id,
        company_id=blueprint.company_id,
        modules=blueprint.modules,
        financial_categories=[
            FinancialCategoryResponse(name=item.name, type=item.type)
            for item in blueprint.financial_categories
        ],
        kpis=[
            KPIResponse(key=item.key, name=item.name, description=item.description)
            for item in blueprint.kpis
        ],
        client_custom_fields=[
            CustomFieldResponse(key=item.key, label=item.label, type=item.type)
            for item in blueprint.client_custom_fields
        ],
        ai_provider=blueprint.ai_provider,
        generated_at=blueprint.generated_at,
    )


@router.post("", response_model=CompanyBlueprintResponse, status_code=status.HTTP_201_CREATED)
async def generate_blueprint(
    payload: GenerateBlueprintRequest,
    company_context: Annotated[
        CompanyContext, Depends(require_role(CompanyRole.OWNER, CompanyRole.ADMIN))
    ],
    company_repository: Annotated[CompanyRepository, Depends(get_company_repository)],
    blueprint_repository: Annotated[
        CompanyBlueprintRepository, Depends(get_company_blueprint_repository)
    ],
    ai_provider: Annotated[AIProviderPort, Depends(get_ai_provider)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> CompanyBlueprintResponse:
    use_case = GenerateCompanyBlueprintUseCase(
        company_repository, blueprint_repository, ai_provider, settings.ai_provider
    )
    blueprint = await use_case.execute(
        company_id=company_context.company_id, additional_context=payload.additional_context
    )
    return _to_response(blueprint)


@router.get("", response_model=CompanyBlueprintResponse)
async def get_blueprint(
    company_context: Annotated[CompanyContext, Depends(get_company_context)],
    blueprint_repository: Annotated[
        CompanyBlueprintRepository, Depends(get_company_blueprint_repository)
    ],
) -> CompanyBlueprintResponse:
    use_case = GetCompanyBlueprintUseCase(blueprint_repository)
    blueprint = await use_case.execute(company_id=company_context.company_id)
    return _to_response(blueprint)
