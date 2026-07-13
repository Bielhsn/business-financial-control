from typing import Protocol

from app.domain.audit.entities import AuditEntry


class AuditLogRepository(Protocol):
    async def create(
        self,
        *,
        company_id: str,
        user_id: str | None,
        action: str,
        details: dict[str, object],
    ) -> AuditEntry: ...

    async def list_for_company(self, company_id: str, *, limit: int = 50) -> list[AuditEntry]: ...
