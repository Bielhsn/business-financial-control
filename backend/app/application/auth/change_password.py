from app.core.exceptions import NotFoundError, UnauthorizedError
from app.domain.auth.ports import PasswordHasher
from app.domain.auth.repository import RefreshTokenRepository
from app.domain.user.repository import UserRepository


class ChangePasswordUseCase:
    def __init__(
        self,
        user_repository: UserRepository,
        refresh_token_repository: RefreshTokenRepository,
        password_hasher: PasswordHasher,
    ) -> None:
        self._user_repository = user_repository
        self._refresh_token_repository = refresh_token_repository
        self._password_hasher = password_hasher

    async def execute(self, *, user_id: str, current_password: str, new_password: str) -> None:
        user = await self._user_repository.get_by_id(user_id)
        if user is None:
            raise NotFoundError("Usuário não encontrado.")
        if not self._password_hasher.verify(current_password, user.hashed_password):
            raise UnauthorizedError("A senha atual está incorreta.")

        await self._user_repository.update(
            user_id, hashed_password=self._password_hasher.hash(new_password)
        )
        # Trocar a senha encerra as demais sessões (segurança).
        await self._refresh_token_repository.revoke_all_for_user(user_id)
