from typing import Protocol

from app.domain.user.entities import User


class UserRepository(Protocol):
    async def get_by_email(self, email: str) -> User | None: ...

    async def delete(self, user_id: str) -> bool:
        """Remove o usuário. Existe para a ação compensatória do cadastro: se a
        empresa não puder ser criada, a conta não pode ficar órfã."""
        ...

    async def get_by_id(self, user_id: str) -> User | None: ...

    async def create(
        self,
        *,
        email: str,
        hashed_password: str,
        full_name: str,
        is_verified: bool = True,
        phone: str | None = None,
        job_role: str | None = None,
    ) -> User: ...

    async def update(self, user_id: str, **fields: object) -> User | None: ...
