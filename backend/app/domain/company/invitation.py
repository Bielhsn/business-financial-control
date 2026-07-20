import secrets
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol

from app.domain.company.roles import CompanyRole


class InvitationStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REVOKED = "revoked"


@dataclass
class Invitation:
    id: str
    company_id: str
    email: str
    role: CompanyRole
    token: str
    status: InvitationStatus
    invited_by: str
    expires_at: datetime
    created_at: datetime


def generate_token() -> str:
    return secrets.token_urlsafe(32)


class InvitationRepository(Protocol):
    async def create(
        self,
        *,
        company_id: str,
        email: str,
        role: CompanyRole,
        token: str,
        invited_by: str,
        expires_at: datetime,
    ) -> Invitation: ...

    async def list_pending_for_company(self, company_id: str) -> list[Invitation]: ...

    async def get_by_token(self, token: str) -> Invitation | None: ...

    async def get_pending_for_email(self, *, company_id: str, email: str) -> Invitation | None: ...

    async def mark_accepted(self, invitation_id: str) -> None: ...

    async def mark_revoked(self, invitation_id: str) -> None: ...
