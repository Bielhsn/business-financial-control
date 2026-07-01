from datetime import UTC, datetime

from app.application.auth.dto import TokenPair
from app.application.auth.token_issuer import issue_token_pair
from app.core.config import Settings
from app.core.exceptions import UnauthorizedError
from app.domain.auth.ports import TokenService
from app.domain.auth.repository import RefreshTokenRepository
from app.domain.user.repository import UserRepository

_INVALID_REFRESH_TOKEN_MESSAGE = "Refresh token inválido ou expirado."


class RefreshAccessTokenUseCase:
    def __init__(
        self,
        user_repository: UserRepository,
        refresh_token_repository: RefreshTokenRepository,
        token_service: TokenService,
        settings: Settings,
    ) -> None:
        self._user_repository = user_repository
        self._refresh_token_repository = refresh_token_repository
        self._token_service = token_service
        self._settings = settings

    async def execute(self, *, raw_refresh_token: str) -> TokenPair:
        token_hash = self._token_service.hash_refresh_token(raw_refresh_token)
        stored_token = await self._refresh_token_repository.get_by_token_hash(token_hash)

        if (
            stored_token is None
            or stored_token.revoked
            or stored_token.expires_at <= datetime.now(UTC)
        ):
            raise UnauthorizedError(_INVALID_REFRESH_TOKEN_MESSAGE)

        user = await self._user_repository.get_by_id(stored_token.user_id)
        if user is None or not user.is_active:
            raise UnauthorizedError(_INVALID_REFRESH_TOKEN_MESSAGE)

        # Rotação: o refresh token usado é revogado e um novo par é emitido.
        await self._refresh_token_repository.revoke(stored_token.id)

        return await issue_token_pair(
            user_id=user.id,
            refresh_token_repository=self._refresh_token_repository,
            token_service=self._token_service,
            settings=self._settings,
        )
