from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.v1.deps import (
    get_audit_log_repository,
    get_company_context,
    get_company_data_eraser,
    get_company_data_exporter,
    get_company_membership_repository,
    get_company_repository,
    get_current_user,
    get_email_sender,
    get_invitation_repository,
    get_user_repository,
    require_role,
)
from app.application.company.create_company import CreateCompanyUseCase
from app.application.company.list_my_companies import ListMyCompaniesUseCase
from app.application.company.team import (
    ChangeMemberRoleUseCase,
    InviteMemberUseCase,
    RemoveMemberUseCase,
)
from app.application.company.update_company import UpdateCompanyUseCase
from app.core.audit import record_audit
from app.core.exceptions import NotFoundError
from app.core.tenant import CompanyContext
from app.domain.audit.repository import AuditLogRepository
from app.domain.company.data import CompanyDataEraser, CompanyDataExporter
from app.domain.company.entities import Company
from app.domain.company.invitation import InvitationRepository
from app.domain.company.repository import CompanyMembershipRepository, CompanyRepository
from app.domain.company.roles import CompanyRole
from app.domain.notifications.email import EmailSender
from app.domain.user.entities import User
from app.domain.user.repository import UserRepository
from app.schemas.company import (
    ChangeRoleRequest,
    CompanyResponse,
    CompanyWithRoleResponse,
    CreateCompanyRequest,
    InvitationResponse,
    InviteMemberRequest,
    MemberResponse,
    UpdateCompanyRequest,
)

router = APIRouter(prefix="/companies", tags=["companies"])

_OWNER_ADMIN = (CompanyRole.OWNER, CompanyRole.ADMIN)


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


# ── Equipe: membros e convites ──────────────────────────────────────────────


@router.get("/{company_id}/members", response_model=list[MemberResponse])
async def list_members(
    company_context: Annotated[CompanyContext, Depends(get_company_context)],
    membership_repository: Annotated[
        CompanyMembershipRepository, Depends(get_company_membership_repository)
    ],
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> list[MemberResponse]:
    memberships = await membership_repository.list_for_company(company_context.company_id)
    members: list[MemberResponse] = []
    for membership in memberships:
        user = await user_repository.get_by_id(membership.user_id)
        if user is None:
            continue
        members.append(
            MemberResponse(
                user_id=user.id, email=user.email, full_name=user.full_name, role=membership.role
            )
        )
    return members


@router.patch("/{company_id}/members/{user_id}", response_model=MemberResponse)
async def change_member_role(
    user_id: str,
    payload: ChangeRoleRequest,
    company_context: Annotated[CompanyContext, Depends(require_role(*_OWNER_ADMIN))],
    current_user: Annotated[User, Depends(get_current_user)],
    membership_repository: Annotated[
        CompanyMembershipRepository, Depends(get_company_membership_repository)
    ],
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
    audit_repository: Annotated[AuditLogRepository, Depends(get_audit_log_repository)],
) -> MemberResponse:
    membership = await ChangeMemberRoleUseCase(membership_repository).execute(
        company_id=company_context.company_id, target_user_id=user_id, role=payload.role
    )
    user = await user_repository.get_by_id(user_id)
    await record_audit(
        audit_repository,
        "member_role_changed",
        user_id=current_user.id,
        company_id=company_context.company_id,
        target_user_id=user_id,
        new_role=payload.role.value,
    )
    return MemberResponse(
        user_id=user_id,
        email=user.email if user else "",
        full_name=user.full_name if user else "",
        role=membership.role,
    )


@router.delete("/{company_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    user_id: str,
    company_context: Annotated[CompanyContext, Depends(require_role(*_OWNER_ADMIN))],
    current_user: Annotated[User, Depends(get_current_user)],
    membership_repository: Annotated[
        CompanyMembershipRepository, Depends(get_company_membership_repository)
    ],
    audit_repository: Annotated[AuditLogRepository, Depends(get_audit_log_repository)],
) -> None:
    await RemoveMemberUseCase(membership_repository).execute(
        company_id=company_context.company_id, target_user_id=user_id
    )
    await record_audit(
        audit_repository,
        "member_removed",
        user_id=current_user.id,
        company_id=company_context.company_id,
        target_user_id=user_id,
    )


@router.post(
    "/{company_id}/invitations",
    response_model=InvitationResponse | None,
    status_code=status.HTTP_201_CREATED,
)
async def invite_member(
    payload: InviteMemberRequest,
    company_context: Annotated[CompanyContext, Depends(require_role(*_OWNER_ADMIN))],
    current_user: Annotated[User, Depends(get_current_user)],
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
    membership_repository: Annotated[
        CompanyMembershipRepository, Depends(get_company_membership_repository)
    ],
    invitation_repository: Annotated[InvitationRepository, Depends(get_invitation_repository)],
    email_sender: Annotated[EmailSender, Depends(get_email_sender)],
    audit_repository: Annotated[AuditLogRepository, Depends(get_audit_log_repository)],
) -> InvitationResponse | None:
    result = await InviteMemberUseCase(
        user_repository, membership_repository, invitation_repository, email_sender
    ).execute(
        company_id=company_context.company_id,
        email=payload.email,
        role=payload.role,
        invited_by=current_user.id,
    )
    await record_audit(
        audit_repository,
        "member_invited",
        user_id=current_user.id,
        company_id=company_context.company_id,
        email=payload.email,
        role=payload.role.value,
        joined_directly=result.membership is not None,
    )
    if result.invitation is None:
        return None  # usuário já existia e virou membro direto
    inv = result.invitation
    return InvitationResponse(
        id=inv.id,
        email=inv.email,
        role=inv.role,
        status=inv.status.value,
        created_at=inv.created_at,
        expires_at=inv.expires_at,
    )


@router.get("/{company_id}/invitations", response_model=list[InvitationResponse])
async def list_invitations(
    company_context: Annotated[CompanyContext, Depends(require_role(*_OWNER_ADMIN))],
    invitation_repository: Annotated[InvitationRepository, Depends(get_invitation_repository)],
) -> list[InvitationResponse]:
    invitations = await invitation_repository.list_pending_for_company(company_context.company_id)
    return [
        InvitationResponse(
            id=inv.id,
            email=inv.email,
            role=inv.role,
            status=inv.status.value,
            created_at=inv.created_at,
            expires_at=inv.expires_at,
        )
        for inv in invitations
    ]


@router.delete("/{company_id}/invitations/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_invitation(
    invitation_id: str,
    company_context: Annotated[CompanyContext, Depends(require_role(*_OWNER_ADMIN))],
    invitation_repository: Annotated[InvitationRepository, Depends(get_invitation_repository)],
) -> None:
    await invitation_repository.mark_revoked(invitation_id)


# ── LGPD: exportação e exclusão ─────────────────────────────────────────────


@router.get("/{company_id}/export")
async def export_company_data(
    company_context: Annotated[CompanyContext, Depends(require_role(CompanyRole.OWNER))],
    current_user: Annotated[User, Depends(get_current_user)],
    exporter: Annotated[CompanyDataExporter, Depends(get_company_data_exporter)],
    audit_repository: Annotated[AuditLogRepository, Depends(get_audit_log_repository)],
) -> dict[str, object]:
    data = await exporter.export(company_context.company_id)
    await record_audit(
        audit_repository,
        "company_data_exported",
        user_id=current_user.id,
        company_id=company_context.company_id,
    )
    return data


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(
    company_context: Annotated[CompanyContext, Depends(require_role(CompanyRole.OWNER))],
    current_user: Annotated[User, Depends(get_current_user)],
    eraser: Annotated[CompanyDataEraser, Depends(get_company_data_eraser)],
    audit_repository: Annotated[AuditLogRepository, Depends(get_audit_log_repository)],
) -> None:
    # Auditar ANTES de apagar (o registro é gravado com company_id explícito).
    await record_audit(
        audit_repository,
        "company_deleted",
        user_id=current_user.id,
        company_id=company_context.company_id,
    )
    await eraser.erase(company_context.company_id)
