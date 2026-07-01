from datetime import UTC, datetime

from beanie import PydanticObjectId

from app.domain.auth.entities import RefreshToken
from app.infrastructure.database.models.refresh_token import RefreshTokenDocument


def _to_entity(document: RefreshTokenDocument) -> RefreshToken:
    return RefreshToken(
        id=str(document.id),
        user_id=document.user_id,
        token_hash=document.token_hash,
        expires_at=document.expires_at,
        revoked=document.revoked,
        created_at=document.created_at,
    )


class BeanieRefreshTokenRepository:
    async def create(self, *, user_id: str, token_hash: str, expires_at: datetime) -> RefreshToken:
        document = RefreshTokenDocument(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            created_at=datetime.now(UTC),
        )
        await document.insert()
        return _to_entity(document)

    async def get_by_token_hash(self, token_hash: str) -> RefreshToken | None:
        document = await RefreshTokenDocument.find_one(
            RefreshTokenDocument.token_hash == token_hash
        )
        return _to_entity(document) if document else None

    async def revoke(self, refresh_token_id: str) -> None:
        if not PydanticObjectId.is_valid(refresh_token_id):
            return
        document = await RefreshTokenDocument.get(PydanticObjectId(refresh_token_id))
        if document is not None:
            document.revoked = True
            await document.save()

    async def revoke_all_for_user(self, user_id: str) -> None:
        await RefreshTokenDocument.find(RefreshTokenDocument.user_id == user_id).update(
            {"$set": {"revoked": True}}
        )
