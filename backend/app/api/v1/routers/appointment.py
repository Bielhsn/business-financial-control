from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.v1.deps import (
    get_appointment_repository,
    get_audit_log_repository,
    get_catalog_item_repository,
    get_client_repository,
    get_company_context,
    get_current_user,
    get_employee_repository,
    get_financial_category_repository,
    get_financial_transaction_repository,
    require_role,
)
from app.application.appointment.change_status import ChangeAppointmentStatusUseCase
from app.application.appointment.create_appointment import CreateAppointmentUseCase
from app.application.appointment.update_appointment import UpdateAppointmentUseCase
from app.core.audit import record_audit
from app.core.exceptions import NotFoundError
from app.core.tenant import CompanyContext
from app.domain.appointment.entities import Appointment
from app.domain.appointment.repository import AppointmentRepository
from app.domain.audit.repository import AuditLogRepository
from app.domain.catalog.repository import CatalogItemRepository
from app.domain.client.repository import ClientRepository
from app.domain.company.roles import CompanyRole
from app.domain.employee.repository import EmployeeRepository
from app.domain.financial.repository import (
    FinancialCategoryRepository,
    FinancialTransactionRepository,
)
from app.domain.user.entities import User
from app.schemas.appointment import (
    AppointmentResponse,
    ChangeAppointmentStatusRequest,
    CreateAppointmentRequest,
    UpdateAppointmentRequest,
)

router = APIRouter(prefix="/companies/{company_id}/appointments", tags=["appointments"])

_STAFF_ROLES = (
    CompanyRole.OWNER,
    CompanyRole.ADMIN,
    CompanyRole.MANAGER,
    CompanyRole.EMPLOYEE,
)


def _to_response(appointment: Appointment) -> AppointmentResponse:
    return AppointmentResponse(
        id=appointment.id,
        company_id=appointment.company_id,
        title=appointment.title,
        starts_at=appointment.starts_at,
        duration_minutes=appointment.duration_minutes,
        status=appointment.status,
        client_id=appointment.client_id,
        client_name=appointment.client_name,
        employee_id=appointment.employee_id,
        employee_name=appointment.employee_name,
        catalog_item_id=appointment.catalog_item_id,
        price_cents=appointment.price_cents,
        notes=appointment.notes,
        revenue_transaction_id=appointment.revenue_transaction_id,
        created_at=appointment.created_at,
        updated_at=appointment.updated_at,
    )


@router.post("", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    payload: CreateAppointmentRequest,
    company_context: Annotated[CompanyContext, Depends(require_role(*_STAFF_ROLES))],
    current_user: Annotated[User, Depends(get_current_user)],
    appointment_repository: Annotated[AppointmentRepository, Depends(get_appointment_repository)],
    client_repository: Annotated[ClientRepository, Depends(get_client_repository)],
    employee_repository: Annotated[EmployeeRepository, Depends(get_employee_repository)],
    catalog_item_repository: Annotated[CatalogItemRepository, Depends(get_catalog_item_repository)],
) -> AppointmentResponse:
    use_case = CreateAppointmentUseCase(
        appointment_repository, client_repository, employee_repository, catalog_item_repository
    )
    appointment = await use_case.execute(
        title=payload.title,
        starts_at=payload.starts_at,
        duration_minutes=payload.duration_minutes,
        client_id=payload.client_id,
        employee_id=payload.employee_id,
        catalog_item_id=payload.catalog_item_id,
        price_cents=payload.price_cents,
        notes=payload.notes,
        created_by=current_user.id,
    )
    return _to_response(appointment)


@router.get("", response_model=list[AppointmentResponse])
async def list_appointments(
    company_context: Annotated[CompanyContext, Depends(get_company_context)],
    appointment_repository: Annotated[AppointmentRepository, Depends(get_appointment_repository)],
    start: Annotated[datetime | None, Query()] = None,
    end: Annotated[datetime | None, Query()] = None,
    employee_id: Annotated[str | None, Query()] = None,
) -> list[AppointmentResponse]:
    # Janela padrão: próximos 30 dias a partir de agora, quando não informada.
    now = datetime.now(UTC)
    window_start = start or now - timedelta(days=1)
    window_end = end or now + timedelta(days=30)
    appointments = await appointment_repository.list_between(
        start=window_start, end=window_end, employee_id=employee_id
    )
    return [_to_response(appointment) for appointment in appointments]


@router.patch("/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    appointment_id: str,
    payload: UpdateAppointmentRequest,
    company_context: Annotated[CompanyContext, Depends(require_role(*_STAFF_ROLES))],
    appointment_repository: Annotated[AppointmentRepository, Depends(get_appointment_repository)],
) -> AppointmentResponse:
    use_case = UpdateAppointmentUseCase(appointment_repository)
    appointment = await use_case.execute(
        appointment_id=appointment_id, **payload.model_dump(exclude_unset=True)
    )
    return _to_response(appointment)


@router.post("/{appointment_id}/status", response_model=AppointmentResponse)
async def change_appointment_status(
    appointment_id: str,
    payload: ChangeAppointmentStatusRequest,
    company_context: Annotated[CompanyContext, Depends(require_role(*_STAFF_ROLES))],
    current_user: Annotated[User, Depends(get_current_user)],
    appointment_repository: Annotated[AppointmentRepository, Depends(get_appointment_repository)],
    category_repository: Annotated[
        FinancialCategoryRepository, Depends(get_financial_category_repository)
    ],
    transaction_repository: Annotated[
        FinancialTransactionRepository, Depends(get_financial_transaction_repository)
    ],
    audit_repository: Annotated[AuditLogRepository, Depends(get_audit_log_repository)],
) -> AppointmentResponse:
    use_case = ChangeAppointmentStatusUseCase(
        appointment_repository, category_repository, transaction_repository
    )
    appointment = await use_case.execute(
        appointment_id=appointment_id, status=payload.status, created_by=current_user.id
    )
    await record_audit(
        audit_repository,
        "appointment_status_changed",
        user_id=current_user.id,
        company_id=company_context.company_id,
        appointment_id=appointment_id,
        new_status=payload.status.value,
        revenue_transaction_id=appointment.revenue_transaction_id,
    )
    return _to_response(appointment)


@router.get("/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(
    appointment_id: str,
    company_context: Annotated[CompanyContext, Depends(get_company_context)],
    appointment_repository: Annotated[AppointmentRepository, Depends(get_appointment_repository)],
) -> AppointmentResponse:
    appointment = await appointment_repository.get_by_id(appointment_id)
    if appointment is None:
        raise NotFoundError("Agendamento não encontrado.")
    return _to_response(appointment)
