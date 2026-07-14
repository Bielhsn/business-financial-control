from typing import Protocol

from app.domain.user.entities import User


class UserRepository(Protocol):
    async def get_by_email(self, email: str) -> User | None: ...

    async def get_by_id(self, user_id: str) -> User | None: ...

    async def create(self, *, email: str, hashed_password: str, full_name: str) -> User: ...
