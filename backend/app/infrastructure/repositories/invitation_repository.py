from datetime import UTC, datetime

from beanie import PydanticObjectId

from app.domain.company.invitation import Invitation, InvitationStatus
from app.domain.company.roles import CompanyRole
from app.infrastructure.database.models.invitation import InvitationDocument


def _to_entity(document: InvitationDocument) -> Invitation:
    return Invitation(
        id=str(document.id),
        company_id=document.company_id,
        email=document.email,
        role=CompanyRole(document.role),
        token=document.token,
        status=InvitationStatus(document.status),
        invited_by=document.invited_by,
        expires_at=document.expires_at,
        created_at=document.created_at,
    )


class BeanieInvitationRepository:
    async def create(
        self,
        *,
        company_id: str,
        email: str,
        role: CompanyRole,
        token: str,
        invited_by: str,
        expires_at: datetime,
    ) -> Invitation:
        document = InvitationDocument(
            company_id=company_id,
            email=email,
            role=role.value,
            token=token,
            status=InvitationStatus.PENDING.value,
            invited_by=invited_by,
            expires_at=expires_at,
            created_at=datetime.now(UTC),
        )
        await document.insert()
        return _to_entity(document)

    async def list_pending_for_company(self, company_id: str) -> list[Invitation]:
        documents = await InvitationDocument.find(
            InvitationDocument.company_id == company_id,
            InvitationDocument.status == InvitationStatus.PENDING.value,
        ).to_list()
        return [_to_entity(document) for document in documents]

    async def get_by_token(self, token: str) -> Invitation | None:
        document = await InvitationDocument.find_one(InvitationDocument.token == token)
        return _to_entity(document) if document else None

    async def get_pending_for_email(self, *, company_id: str, email: str) -> Invitation | None:
        document = await InvitationDocument.find_one(
            InvitationDocument.company_id == company_id,
            InvitationDocument.email == email,
            InvitationDocument.status == InvitationStatus.PENDING.value,
        )
        return _to_entity(document) if document else None

    async def mark_accepted(self, invitation_id: str) -> None:
        await self._set_status(invitation_id, InvitationStatus.ACCEPTED)

    async def mark_revoked(self, invitation_id: str) -> None:
        await self._set_status(invitation_id, InvitationStatus.REVOKED)

    async def _set_status(self, invitation_id: str, status: InvitationStatus) -> None:
        if not PydanticObjectId.is_valid(invitation_id):
            return
        document = await InvitationDocument.get(PydanticObjectId(invitation_id))
        if document is not None:
            document.status = status.value
            await document.save()
