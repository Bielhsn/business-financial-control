from app.domain.auth.ports import TokenService
from app.domain.auth.repository import RefreshTokenRepository


class LogoutUseCase:
    """Revoga um refresh token. Idempotente: nunca revela se o token era válido."""

    def __init__(
        self, refresh_token_repository: RefreshTokenRepository, token_service: TokenService
    ) -> None:
        self._refresh_token_repository = refresh_token_repository
        self._token_service = token_service

    async def execute(self, *, raw_refresh_token: str) -> None:
        token_hash = self._token_service.hash_refresh_token(raw_refresh_token)
        stored_token = await self._refresh_token_repository.get_by_token_hash(token_hash)
        if stored_token is not None and not stored_token.revoked:
            await self._refresh_token_repository.revoke(stored_token.id)
