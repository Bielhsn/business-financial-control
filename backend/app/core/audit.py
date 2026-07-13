"""Trilha de auditoria de ações sensíveis.

Eventos estruturados via structlog (JSON em produção): cada ação sensível emite um
`audit_event` com ator, empresa e detalhes — agregáveis por qualquer coletor de logs
(Datadog, Loki, CloudWatch...). Persistência em banco dedicado é evolução futura; a
trilha em log já é imutável no destino e não acopla auditoria à disponibilidade do
MongoDB.
"""

from typing import TYPE_CHECKING, Any

from app.core.logging import get_logger

if TYPE_CHECKING:
    from app.domain.audit.repository import AuditLogRepository

_audit_logger = get_logger("audit")


async def record_audit(
    repository: "AuditLogRepository",
    action: str,
    *,
    company_id: str,
    user_id: str | None = None,
    **details: Any,
) -> None:
    """Registra a ação no log estruturado E na trilha persistida da empresa."""
    audit_event(action, user_id=user_id, company_id=company_id, **details)
    await repository.create(
        company_id=company_id, user_id=user_id, action=action, details=dict(details)
    )


def audit_event(
    action: str,
    *,
    user_id: str | None = None,
    company_id: str | None = None,
    **details: Any,
) -> None:
    _audit_logger.info(
        "audit_event",
        action=action,
        user_id=user_id,
        company_id=company_id,
        **details,
    )
