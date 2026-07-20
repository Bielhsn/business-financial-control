from datetime import UTC, datetime

from app.domain.auth.verification import VerificationCode, VerificationPurpose
from app.infrastructure.database.models.verification_code import VerificationCodeDocument


def _to_entity(document: VerificationCodeDocument) -> VerificationCode:
    return VerificationCode(
        id=str(document.id),
        user_id=document.user_id,
        purpose=VerificationPurpose(document.purpose),
        code_hash=document.code_hash,
        expires_at=document.expires_at,
        used=document.used,
        created_at=document.created_at,
    )


class BeanieVerificationCodeRepository:
    async def create(
        self,
        *,
        user_id: str,
        purpose: VerificationPurpose,
        code_hash: str,
        expires_at: datetime,
    ) -> VerificationCode:
        document = VerificationCodeDocument(
            user_id=user_id,
            purpose=purpose.value,
            code_hash=code_hash,
            expires_at=expires_at,
            created_at=datetime.now(UTC),
        )
        await document.insert()
        return _to_entity(document)

    async def get_active(
        self, *, user_id: str, purpose: VerificationPurpose, code_hash: str
    ) -> VerificationCode | None:
        document = await VerificationCodeDocument.find_one(
            VerificationCodeDocument.user_id == user_id,
            VerificationCodeDocument.purpose == purpose.value,
            VerificationCodeDocument.code_hash == code_hash,
            VerificationCodeDocument.used == False,  # noqa: E712
        )
        if document is None:
            return None
        expires = document.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=UTC)
        if expires < datetime.now(UTC):
            return None
        return _to_entity(document)

    async def mark_used(self, code_id: str) -> None:
        from beanie import PydanticObjectId

        if not PydanticObjectId.is_valid(code_id):
            return
        document = await VerificationCodeDocument.get(PydanticObjectId(code_id))
        if document is not None:
            document.used = True
            await document.save()

    async def invalidate_for(self, *, user_id: str, purpose: VerificationPurpose) -> None:
        await VerificationCodeDocument.find(
            VerificationCodeDocument.user_id == user_id,
            VerificationCodeDocument.purpose == purpose.value,
            VerificationCodeDocument.used == False,  # noqa: E712
        ).update({"$set": {"used": True}})
