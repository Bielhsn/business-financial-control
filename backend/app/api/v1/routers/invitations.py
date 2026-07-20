from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.v1.deps import (
    get_company_membership_repository,
    get_company_repository,
    get_current_user,
    get_invitation_repository,
    get_user_repository,
)
from app.application.company.team import AcceptInvitationUseCase
from app.core.exceptions import NotFoundError
from app.domain.company.invitation import InvitationRepository
from app.domain.company.repository import CompanyMembershipRepository, CompanyRepository
from app.domain.user.entities import User
from app.domain.user.repository import UserRepository
from app.schemas.company import AcceptInvitationRequest, CompanyResponse, CompanyWithRoleResponse

router = APIRouter(prefix="/invitations", tags=["invitations"])


# Aceite não é company-scoped: o usuário logado aceita um convite pelo token.
@router.post("/accept", response_model=CompanyWithRoleResponse)
async def accept_invitation(
    payload: AcceptInvitationRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
    membership_repository: Annotated[
        CompanyMembershipRepository, Depends(get_company_membership_repository)
    ],
    invitation_repository: Annotated[InvitationRepository, Depends(get_invitation_repository)],
    company_repository: Annotated[CompanyRepository, Depends(get_company_repository)],
) -> CompanyWithRoleResponse:
    membership = await AcceptInvitationUseCase(
        user_repository, membership_repository, invitation_repository
    ).execute(token=payload.token, user_id=current_user.id)

    company = await company_repository.get_by_id(membership.company_id)
    if company is None:
        raise NotFoundError("Empresa não encontrada.")
    return CompanyWithRoleResponse(
        company=CompanyResponse.model_validate(company), role=membership.role
    )
