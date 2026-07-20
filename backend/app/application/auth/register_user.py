from app.core.config import Settings
from app.core.exceptions import ConflictError
from app.domain.auth.ports import PasswordHasher
from app.domain.user.entities import User
from app.domain.user.repository import UserRepository


class RegisterUserUseCase:
    def __init__(
        self,
        user_repository: UserRepository,
        password_hasher: PasswordHasher,
        settings: Settings,
    ) -> None:
        self._user_repository = user_repository
        self._password_hasher = password_hasher
        self._settings = settings

    async def execute(self, *, email: str, password: str, full_name: str) -> User:
        normalized_email = email.strip().lower()

        if await self._user_repository.get_by_email(normalized_email) is not None:
            raise ConflictError("Já existe uma conta com este e-mail.")

        hashed_password = self._password_hasher.hash(password)
        # Se a verificação por e-mail está ligada, a conta nasce não verificada e
        # precisa confirmar o código antes de logar.
        return await self._user_repository.create(
            email=normalized_email,
            hashed_password=hashed_password,
            full_name=full_name.strip(),
            is_verified=not self._settings.require_email_verification,
        )
