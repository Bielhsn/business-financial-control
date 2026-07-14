from datetime import UTC, datetime

from beanie import PydanticObjectId
from pymongo.errors import DuplicateKeyError

from app.core.exceptions import ConflictError
from app.domain.company.entities import CompanyMembership
from app.domain.company.roles import CompanyRole
from app.infrastructure.database.models.company_membership import CompanyMembershipDocument


def _to_entity(document: CompanyMembershipDocument) -> CompanyMembership:
    return CompanyMembership(
        id=str(document.id),
        company_id=document.company_id,
        user_id=document.user_id,
        role=CompanyRole(document.role),
        created_at=document.created_at,
    )


class BeanieCompanyMembershipRepository:
    async def create(
        self, *, company_id: str, user_id: str, role: CompanyRole
    ) -> CompanyMembership:
        document = CompanyMembershipDocument(
            company_id=company_id,
            user_id=user_id,
            role=role.value,
            created_at=datetime.now(UTC),
        )
        try:
            await document.insert()
        except DuplicateKeyError as exc:
            raise ConflictError("Usuário já é membro desta empresa.") from exc
        return _to_entity(document)

    async def get_by_user_and_company(
        self, user_id: str, company_id: str
    ) -> CompanyMembership | None:
        document = await CompanyMembershipDocument.find_one(
            CompanyMembershipDocument.user_id == user_id,
            CompanyMembershipDocument.company_id == company_id,
        )
        return _to_entity(document) if document else None

    async def list_for_user(self, user_id: str) -> list[CompanyMembership]:
        documents = await CompanyMembershipDocument.find(
            CompanyMembershipDocument.user_id == user_id
        ).to_list()
        return [_to_entity(document) for document in documents]

    async def delete(self, membership_id: str) -> None:
        if not PydanticObjectId.is_valid(membership_id):
            return
        document = await CompanyMembershipDocument.get(PydanticObjectId(membership_id))
        if document is not None:
            await document.delete()
