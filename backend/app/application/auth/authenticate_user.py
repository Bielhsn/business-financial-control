from app.application.auth.dto import TokenPair
from app.application.auth.token_issuer import issue_token_pair
from app.core.config import Settings
from app.core.exceptions import UnauthorizedError
from app.domain.auth.ports import PasswordHasher, TokenService
from app.domain.auth.repository import RefreshTokenRepository
from app.domain.user.repository import UserRepository

_INVALID_CREDENTIALS_MESSAGE = "E-mail ou senha inválidos."


class AuthenticateUserUseCase:
    def __init__(
        self,
        user_repository: UserRepository,
        refresh_token_repository: RefreshTokenRepository,
        password_hasher: PasswordHasher,
        token_service: TokenService,
        settings: Settings,
    ) -> None:
        self._user_repository = user_repository
        self._refresh_token_repository = refresh_token_repository
        self._password_hasher = password_hasher
        self._token_service = token_service
        self._settings = settings

    async def execute(self, *, email: str, password: str) -> TokenPair:
        user = await self._user_repository.get_by_email(email.strip().lower())

        if user is None or not user.is_active:
            raise UnauthorizedError(_INVALID_CREDENTIALS_MESSAGE)

        if not self._password_hasher.verify(password, user.hashed_password):
            raise UnauthorizedError(_INVALID_CREDENTIALS_MESSAGE)

        return await issue_token_pair(
            user_id=user.id,
            refresh_token_repository=self._refresh_token_repository,
            token_service=self._token_service,
            settings=self._settings,
        )
