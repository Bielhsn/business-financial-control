from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.v1.deps import (
    get_audit_log_repository,
    get_company_context,
    get_company_membership_repository,
    get_company_repository,
    get_current_user,
    require_role,
)
from app.application.company.create_company import CreateCompanyUseCase
from app.application.company.list_my_companies import ListMyCompaniesUseCase
from app.application.company.update_company import UpdateCompanyUseCase
from app.core.audit import record_audit
from app.core.exceptions import NotFoundError
from app.core.tenant import CompanyContext
from app.domain.audit.repository import AuditLogRepository
from app.domain.company.entities import Company
from app.domain.company.repository import CompanyMembershipRepository, CompanyRepository
from app.domain.company.roles import CompanyRole
from app.domain.user.entities import User
from app.schemas.company import (
    CompanyResponse,
    CompanyWithRoleResponse,
    CreateCompanyRequest,
    UpdateCompanyRequest,
)

router = APIRouter(prefix="/companies", tags=["companies"])


@router.post("", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
async def create_company(
    payload: CreateCompanyRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    company_repository: Annotated[CompanyRepository, Depends(get_company_repository)],
    membership_repository: Annotated[
        CompanyMembershipRepository, Depends(get_company_membership_repository)
    ],
) -> Company:
    use_case = CreateCompanyUseCase(company_repository, membership_repository)
    return await use_case.execute(owner_id=current_user.id, **payload.model_dump())


@router.get("", response_model=list[CompanyWithRoleResponse])
async def list_my_companies(
    current_user: Annotated[User, Depends(get_current_user)],
    company_repository: Annotated[CompanyRepository, Depends(get_company_repository)],
    membership_repository: Annotated[
        CompanyMembershipRepository, Depends(get_company_membership_repository)
    ],
) -> list[CompanyWithRoleResponse]:
    use_case = ListMyCompaniesUseCase(membership_repository, company_repository)
    items = await use_case.execute(user_id=current_user.id)
    return [
        CompanyWithRoleResponse(
            company=CompanyResponse.model_validate(item.company), role=item.role
        )
        for item in items
    ]


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_context: Annotated[CompanyContext, Depends(get_company_context)],
    company_repository: Annotated[CompanyRepository, Depends(get_company_repository)],
) -> Company:
    company = await company_repository.get_by_id(company_context.company_id)
    if company is None:
        raise NotFoundError("Empresa não encontrada.")
    return company


@router.patch("/{company_id}", response_model=CompanyResponse)
async def update_company(
    payload: UpdateCompanyRequest,
    company_context: Annotated[
        CompanyContext, Depends(require_role(CompanyRole.OWNER, CompanyRole.ADMIN))
    ],
    current_user: Annotated[User, Depends(get_current_user)],
    company_repository: Annotated[CompanyRepository, Depends(get_company_repository)],
    audit_repository: Annotated[AuditLogRepository, Depends(get_audit_log_repository)],
) -> Company:
    use_case = UpdateCompanyUseCase(company_repository)
    company = await use_case.execute(
        company_id=company_context.company_id, **payload.model_dump(exclude_unset=True)
    )
    await record_audit(
        audit_repository,
        "company_updated",
        user_id=current_user.id,
        company_id=company_context.company_id,
        fields=sorted(payload.model_dump(exclude_unset=True).keys()),
    )
    return company
