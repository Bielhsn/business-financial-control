from datetime import UTC, datetime

from beanie import PydanticObjectId
from pymongo.errors import DuplicateKeyError

from app.core.exceptions import ConflictError
from app.domain.user.entities import User
from app.infrastructure.database.models.user import UserDocument


def _to_entity(document: UserDocument) -> User:
    return User(
        id=str(document.id),
        email=document.email,
        hashed_password=document.hashed_password,
        full_name=document.full_name,
        is_active=document.is_active,
        is_verified=document.is_verified,
        created_at=document.created_at,
        updated_at=document.updated_at,
    )


class BeanieUserRepository:
    async def get_by_email(self, email: str) -> User | None:
        document = await UserDocument.find_one(UserDocument.email == email)
        return _to_entity(document) if document else None

    async def get_by_id(self, user_id: str) -> User | None:
        if not PydanticObjectId.is_valid(user_id):
            return None
        document = await UserDocument.get(PydanticObjectId(user_id))
        return _to_entity(document) if document else None

    async def create(
        self,
        *,
        email: str,
        hashed_password: str,
        full_name: str,
        is_verified: bool = True,
    ) -> User:
        now = datetime.now(UTC)
        document = UserDocument(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            is_verified=is_verified,
            created_at=now,
            updated_at=now,
        )
        try:
            await document.insert()
        except DuplicateKeyError as exc:
            raise ConflictError("Já existe uma conta com este e-mail.") from exc
        return _to_entity(document)

    async def update(self, user_id: str, **fields: object) -> User | None:
        if not PydanticObjectId.is_valid(user_id):
            return None
        document = await UserDocument.get(PydanticObjectId(user_id))
        if document is None:
            return None
        for field_name, value in fields.items():
            setattr(document, field_name, value)
        document.updated_at = datetime.now(UTC)
        await document.save()
        return _to_entity(document)
