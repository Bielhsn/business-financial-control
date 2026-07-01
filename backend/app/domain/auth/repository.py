from datetime import datetime
from typing import Protocol

from app.domain.auth.entities import RefreshToken


class RefreshTokenRepository(Protocol):
    async def create(
        self, *, user_id: str, token_hash: str, expires_at: datetime
    ) -> RefreshToken: ...

    async def get_by_token_hash(self, token_hash: str) -> RefreshToken | None: ...

    async def revoke(self, refresh_token_id: str) -> None: ...

    async def revoke_all_for_user(self, user_id: str) -> None: ...
