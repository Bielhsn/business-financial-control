from datetime import UTC, datetime

from beanie import PydanticObjectId

from app.core.tenant import get_current_company_id
from app.domain.apikey.entities import ApiKey
from app.infrastructure.database.models.api_key import ApiKeyDocument


def _to_entity(document: ApiKeyDocument) -> ApiKey:
    return ApiKey(
        id=str(document.id),
        company_id=document.company_id,
        name=document.name,
        prefix=document.prefix,
        created_at=document.created_at,
        last_used_at=document.last_used_at,
        revoked=document.revoked,
    )


class BeanieApiKeyRepository:
    async def create(self, *, name: str, prefix: str, hashed_key: str) -> ApiKey:
        document = ApiKeyDocument(
            company_id=get_current_company_id(),
            name=name,
            prefix=prefix,
            hashed_key=hashed_key,
            created_at=datetime.now(UTC),
        )
        await document.insert()
        return _to_entity(document)

    async def list_for_company(self) -> list[ApiKey]:
        company_id = get_current_company_id()
        documents = await ApiKeyDocument.find(ApiKeyDocument.company_id == company_id).to_list()
        return [_to_entity(document) for document in documents]

    async def get_active_by_hash(self, hashed_key: str) -> ApiKey | None:
        # Cross-tenant de propósito: a requisição só traz a chave.
        document = await ApiKeyDocument.find_one(
            ApiKeyDocument.hashed_key == hashed_key,
            ApiKeyDocument.revoked == False,  # noqa: E712
        )
        return _to_entity(document) if document else None

    async def revoke(self, key_id: str) -> bool:
        if not PydanticObjectId.is_valid(key_id):
            return False
        company_id = get_current_company_id()
        document = await ApiKeyDocument.find_one(
            ApiKeyDocument.id == PydanticObjectId(key_id),
            ApiKeyDocument.company_id == company_id,
        )
        if document is None:
            return False
        document.revoked = True
        await document.save()
        return True

    async def touch_last_used(self, key_id: str) -> None:
        if not PydanticObjectId.is_valid(key_id):
            return
        document = await ApiKeyDocument.get(PydanticObjectId(key_id))
        if document is not None:
            document.last_used_at = datetime.now(UTC)
            await document.save()
