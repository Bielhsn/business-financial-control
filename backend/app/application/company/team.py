from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.domain.company.entities import CompanyMembership
from app.domain.company.invitation import (
    Invitation,
    InvitationRepository,
    InvitationStatus,
    generate_token,
)
from app.domain.company.repository import CompanyMembershipRepository
from app.domain.company.roles import CompanyRole
from app.domain.notifications.email import EmailMessage, EmailSender
from app.domain.user.repository import UserRepository

_INVITE_TTL_DAYS = 7


@dataclass
class InviteResult:
    invitation: Invitation | None
    membership: CompanyMembership | None


class InviteMemberUseCase:
    """Convida alguém para a empresa. Se o e-mail já tem conta, vira membro na
    hora; senão, cria um convite pendente e envia um e-mail com o código/token."""

    def __init__(
        self,
        user_repository: UserRepository,
        membership_repository: CompanyMembershipRepository,
        invitation_repository: InvitationRepository,
        email_sender: EmailSender,
    ) -> None:
        self._user_repository = user_repository
        self._membership_repository = membership_repository
        self._invitation_repository = invitation_repository
        self._email_sender = email_sender

    async def execute(
        self, *, company_id: str, email: str, role: CompanyRole, invited_by: str
    ) -> InviteResult:
        if role == CompanyRole.OWNER:
            raise ValidationError("Não é possível convidar alguém como proprietário.")
        normalized = email.strip().lower()

        existing_user = await self._user_repository.get_by_email(normalized)
        if existing_user is not None:
            already = await self._membership_repository.get_by_user_and_company(
                existing_user.id, company_id
            )
            if already is not None:
                raise ConflictError("Este usuário já faz parte da empresa.")
            membership = await self._membership_repository.create(
                company_id=company_id, user_id=existing_user.id, role=role
            )
            await self._email_sender.send(
                EmailMessage(
                    to=normalized,
                    subject="Você foi adicionado a uma empresa no Aurum OS",
                    body="Você já tem conta e agora faz parte de uma nova empresa. "
                    "Entre no Aurum OS para acessá-la.",
                )
            )
            return InviteResult(invitation=None, membership=membership)

        pending = await self._invitation_repository.get_pending_for_email(
            company_id=company_id, email=normalized
        )
        if pending is not None:
            raise ConflictError("Já existe um convite pendente para este e-mail.")

        token = generate_token()
        invitation = await self._invitation_repository.create(
            company_id=company_id,
            email=normalized,
            role=role,
            token=token,
            invited_by=invited_by,
            expires_at=datetime.now(UTC) + timedelta(days=_INVITE_TTL_DAYS),
        )
        await self._email_sender.send(
            EmailMessage(
                to=normalized,
                subject="Convite para o Aurum OS",
                body="Você foi convidado para uma empresa no Aurum OS. "
                f"Crie sua conta e use este código de convite: {token}",
            )
        )
        return InviteResult(invitation=invitation, membership=None)


class AcceptInvitationUseCase:
    def __init__(
        self,
        user_repository: UserRepository,
        membership_repository: CompanyMembershipRepository,
        invitation_repository: InvitationRepository,
    ) -> None:
        self._user_repository = user_repository
        self._membership_repository = membership_repository
        self._invitation_repository = invitation_repository

    async def execute(self, *, token: str, user_id: str) -> CompanyMembership:
        invitation = await self._invitation_repository.get_by_token(token.strip())
        if invitation is None or invitation.status != InvitationStatus.PENDING:
            raise ValidationError("Convite inválido ou já utilizado.")
        expires = invitation.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=UTC)
        if expires < datetime.now(UTC):
            raise ValidationError("Convite expirado.")

        user = await self._user_repository.get_by_id(user_id)
        if user is None:
            raise NotFoundError("Usuário não encontrado.")
        if user.email.strip().lower() != invitation.email:
            raise ValidationError("Este convite foi enviado para outro e-mail.")

        existing = await self._membership_repository.get_by_user_and_company(
            user_id, invitation.company_id
        )
        if existing is not None:
            await self._invitation_repository.mark_accepted(invitation.id)
            return existing

        membership = await self._membership_repository.create(
            company_id=invitation.company_id, user_id=user_id, role=invitation.role
        )
        await self._invitation_repository.mark_accepted(invitation.id)
        return membership


async def _assert_not_last_owner(
    membership_repository: CompanyMembershipRepository,
    *,
    company_id: str,
    target: CompanyMembership,
) -> None:
    """Impede remover/rebaixar o último proprietário — a empresa nunca fica sem dono."""
    if target.role != CompanyRole.OWNER:
        return
    members = await membership_repository.list_for_company(company_id)
    owners = [m for m in members if m.role == CompanyRole.OWNER]
    if len(owners) <= 1:
        raise ValidationError("A empresa precisa de ao menos um proprietário.")


class ChangeMemberRoleUseCase:
    def __init__(self, membership_repository: CompanyMembershipRepository) -> None:
        self._membership_repository = membership_repository

    async def execute(
        self, *, company_id: str, target_user_id: str, role: CompanyRole
    ) -> CompanyMembership:
        target = await self._membership_repository.get_by_user_and_company(
            target_user_id, company_id
        )
        if target is None:
            raise NotFoundError("Membro não encontrado.")
        if role != CompanyRole.OWNER:
            await _assert_not_last_owner(
                self._membership_repository, company_id=company_id, target=target
            )
        updated = await self._membership_repository.update_role(target.id, role)
        if updated is None:
            raise NotFoundError("Membro não encontrado.")
        return updated


class RemoveMemberUseCase:
    def __init__(self, membership_repository: CompanyMembershipRepository) -> None:
        self._membership_repository = membership_repository

    async def execute(self, *, company_id: str, target_user_id: str) -> None:
        target = await self._membership_repository.get_by_user_and_company(
            target_user_id, company_id
        )
        if target is None:
            raise NotFoundError("Membro não encontrado.")
        await _assert_not_last_owner(
            self._membership_repository, company_id=company_id, target=target
        )
        await self._membership_repository.delete(target.id)
