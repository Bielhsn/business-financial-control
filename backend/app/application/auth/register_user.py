from app.core.exceptions import ConflictError
from app.domain.auth.ports import PasswordHasher
from app.domain.user.entities import User
from app.domain.user.repository import UserRepository


class RegisterUserUseCase:
    def __init__(self, user_repository: UserRepository, password_hasher: PasswordHasher) -> None:
        self._user_repository = user_repository
        self._password_hasher = password_hasher

    async def execute(self, *, email: str, password: str, full_name: str) -> User:
        normalized_email = email.strip().lower()

        if await self._user_repository.get_by_email(normalized_email) is not None:
            raise ConflictError("Já existe uma conta com este e-mail.")

        hashed_password = self._password_hasher.hash(password)
        return await self._user_repository.create(
            email=normalized_email,
            hashed_password=hashed_password,
            full_name=full_name.strip(),
        )
