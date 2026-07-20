import secrets

from app.application.auth.dto import TokenPair
from app.application.auth.token_issuer import issue_token_pair
from app.core.config import Settings
from app.domain.auth.google import GoogleTokenVerifier
from app.domain.auth.ports import PasswordHasher, TokenService
from app.domain.auth.repository import RefreshTokenRepository
from app.domain.user.repository import UserRepository


class LoginWithGoogleUseCase:
    """Valida o id_token do Google e loga o usuário, criando a conta na primeira
    vez (find-or-create por e-mail). Contas via Google já entram verificadas."""

    def __init__(
        self,
        user_repository: UserRepository,
        refresh_token_repository: RefreshTokenRepository,
        password_hasher: PasswordHasher,
        token_service: TokenService,
        google_verifier: GoogleTokenVerifier,
        settings: Settings,
    ) -> None:
        self._user_repository = user_repository
        self._refresh_token_repository = refresh_token_repository
        self._password_hasher = password_hasher
        self._token_service = token_service
        self._google_verifier = google_verifier
        self._settings = settings

    async def execute(self, *, id_token: str) -> TokenPair:
        identity = await self._google_verifier.verify(id_token)

        user = await self._user_repository.get_by_email(identity.email)
        if user is None:
            # Senha aleatória inutilizável: o acesso é só via Google até o usuário
            # definir uma senha por "esqueci minha senha", se quiser.
            random_password = self._password_hasher.hash(secrets.token_urlsafe(32))
            user = await self._user_repository.create(
                email=identity.email,
                hashed_password=random_password,
                full_name=identity.full_name,
                is_verified=True,
            )
        elif not user.is_verified:
            # E-mail confirmado pelo Google → marca como verificado.
            await self._user_repository.update(user.id, is_verified=True)

        return await issue_token_pair(
            user_id=user.id,
            refresh_token_repository=self._refresh_token_repository,
            token_service=self._token_service,
            settings=self._settings,
        )
