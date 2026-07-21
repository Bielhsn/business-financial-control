from dataclasses import dataclass

from app.domain.apikey.entities import (
    ApiKey,
    ApiKeyRepository,
    api_key_prefix,
    generate_api_key,
    hash_api_key,
)


@dataclass
class CreatedApiKey:
    api_key: ApiKey
    raw_key: str  # mostrado UMA única vez


class CreateApiKeyUseCase:
    def __init__(self, repository: ApiKeyRepository, *, secret: str) -> None:
        self._repository = repository
        self._secret = secret

    async def execute(self, *, name: str) -> CreatedApiKey:
        raw = generate_api_key()
        api_key = await self._repository.create(
            name=name,
            prefix=api_key_prefix(raw),
            hashed_key=hash_api_key(raw, secret=self._secret),
        )
        return CreatedApiKey(api_key=api_key, raw_key=raw)
