from datetime import UTC, datetime
from typing import Any

from app.core.exceptions import UnauthorizedError
from app.domain.auth.entities import RefreshToken
from app.domain.company.entities import Company, CompanyMembership
from app.domain.company.roles import CompanyRole
from app.domain.user.entities import User


class FakeUserRepository:
    def __init__(self) -> None:
        self._users_by_id: dict[str, User] = {}
        self._next_id = 1

    async def get_by_email(self, email: str) -> User | None:
        return next((u for u in self._users_by_id.values() if u.email == email), None)

    async def get_by_id(self, user_id: str) -> User | None:
        return self._users_by_id.get(user_id)

    async def create(self, *, email: str, hashed_password: str, full_name: str) -> User:
        user_id = str(self._next_id)
        self._next_id += 1
        now = datetime.now(UTC)
        user = User(
            id=user_id,
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        self._users_by_id[user_id] = user
        return user


class FakeRefreshTokenRepository:
    def __init__(self) -> None:
        self._tokens: dict[str, RefreshToken] = {}
        self._next_id = 1

    async def create(self, *, user_id: str, token_hash: str, expires_at: datetime) -> RefreshToken:
        token_id = str(self._next_id)
        self._next_id += 1
        token = RefreshToken(
            id=token_id,
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            revoked=False,
            created_at=datetime.now(UTC),
        )
        self._tokens[token_id] = token
        return token

    async def get_by_token_hash(self, token_hash: str) -> RefreshToken | None:
        return next((t for t in self._tokens.values() if t.token_hash == token_hash), None)

    async def revoke(self, refresh_token_id: str) -> None:
        token = self._tokens.get(refresh_token_id)
        if token is not None:
            token.revoked = True

    async def revoke_all_for_user(self, user_id: str) -> None:
        for token in self._tokens.values():
            if token.user_id == user_id:
                token.revoked = True


class FakePasswordHasher:
    def hash(self, password: str) -> str:
        return f"hashed:{password}"

    def verify(self, password: str, hashed_password: str) -> bool:
        return hashed_password == f"hashed:{password}"


class FakeTokenService:
    def __init__(self) -> None:
        self._counter = 0

    def create_access_token(self, subject: str) -> str:
        return f"access:{subject}"

    def decode_access_token(self, token: str) -> dict[str, Any]:
        if not token.startswith("access:"):
            raise UnauthorizedError("Token inválido ou expirado.")
        return {"sub": token.removeprefix("access:")}

    def generate_refresh_token(self) -> str:
        self._counter += 1
        return f"refresh-raw-{self._counter}"

    def hash_refresh_token(self, raw_token: str) -> str:
        return f"hash:{raw_token}"


class FakeCompanyRepository:
    def __init__(self) -> None:
        self._companies: dict[str, Company] = {}
        self._next_id = 1

    async def create(
        self,
        *,
        name: str,
        segment: str,
        employee_count: int,
        average_customer_count: int,
        city: str,
        state: str,
        country: str,
        size: str,
        tax_regime: str | None,
        additional_info: str | None,
    ) -> Company:
        company_id = str(self._next_id)
        self._next_id += 1
        now = datetime.now(UTC)
        company = Company(
            id=company_id,
            name=name,
            segment=segment,
            employee_count=employee_count,
            average_customer_count=average_customer_count,
            city=city,
            state=state,
            country=country,
            size=size,
            tax_regime=tax_regime,
            additional_info=additional_info,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        self._companies[company_id] = company
        return company

    async def get_by_id(self, company_id: str) -> Company | None:
        return self._companies.get(company_id)

    async def update(self, company_id: str, **fields: object) -> Company | None:
        company = self._companies.get(company_id)
        if company is None:
            return None
        for key, value in fields.items():
            setattr(company, key, value)
        company.updated_at = datetime.now(UTC)
        return company

    async def delete(self, company_id: str) -> None:
        self._companies.pop(company_id, None)


class FakeCompanyMembershipRepository:
    def __init__(self) -> None:
        self._memberships: dict[str, CompanyMembership] = {}
        self._next_id = 1
        self.fail_on_create = False

    async def create(
        self, *, company_id: str, user_id: str, role: CompanyRole
    ) -> CompanyMembership:
        if self.fail_on_create:
            raise RuntimeError("Falha simulada ao criar vínculo.")
        membership_id = str(self._next_id)
        self._next_id += 1
        membership = CompanyMembership(
            id=membership_id,
            company_id=company_id,
            user_id=user_id,
            role=role,
            created_at=datetime.now(UTC),
        )
        self._memberships[membership_id] = membership
        return membership

    async def get_by_user_and_company(
        self, user_id: str, company_id: str
    ) -> CompanyMembership | None:
        return next(
            (
                m
                for m in self._memberships.values()
                if m.user_id == user_id and m.company_id == company_id
            ),
            None,
        )

    async def list_for_user(self, user_id: str) -> list[CompanyMembership]:
        return [m for m in self._memberships.values() if m.user_id == user_id]

    async def delete(self, membership_id: str) -> None:
        self._memberships.pop(membership_id, None)
