from datetime import UTC, datetime

from app.domain.audit.entities import AuditEntry
from app.infrastructure.database.models.audit_log import AuditLogDocument


def _to_entity(document: AuditLogDocument) -> AuditEntry:
    return AuditEntry(
        id=str(document.id),
        company_id=document.company_id,
        user_id=document.user_id,
        action=document.action,
        details=document.details,
        created_at=document.created_at,
    )


class BeanieAuditLogRepository:
    """Auditoria recebe company_id explícito (não usa o contexto de tenant):
    a trilha também registra eventos fora de um request tenant-scoped."""

    async def create(
        self,
        *,
        company_id: str,
        user_id: str | None,
        action: str,
        details: dict[str, object],
    ) -> AuditEntry:
        document = AuditLogDocument(
            company_id=company_id,
            user_id=user_id,
            action=action,
            details=details,
            created_at=datetime.now(UTC),
        )
        await document.insert()
        return _to_entity(document)

    async def list_for_company(self, company_id: str, *, limit: int = 50) -> list[AuditEntry]:
        documents = (
            await AuditLogDocument.find({"company_id": company_id})
            .sort("-created_at")
            .limit(limit)
            .to_list()
        )
        return [_to_entity(document) for document in documents]
