from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.v1.deps import get_audit_log_repository, require_role
from app.core.tenant import CompanyContext
from app.domain.audit.repository import AuditLogRepository
from app.domain.company.roles import CompanyRole
from app.schemas.audit import AuditEntryResponse

router = APIRouter(prefix="/companies/{company_id}/audit-logs", tags=["audit"])


@router.get("", response_model=list[AuditEntryResponse])
async def list_audit_logs(
    company_context: Annotated[
        CompanyContext, Depends(require_role(CompanyRole.OWNER, CompanyRole.ADMIN))
    ],
    audit_repository: Annotated[AuditLogRepository, Depends(get_audit_log_repository)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[AuditEntryResponse]:
    entries = await audit_repository.list_for_company(company_context.company_id, limit=limit)
    return [
        AuditEntryResponse(
            id=entry.id,
            user_id=entry.user_id,
            action=entry.action,
            details=entry.details,
            created_at=entry.created_at,
        )
        for entry in entries
    ]
