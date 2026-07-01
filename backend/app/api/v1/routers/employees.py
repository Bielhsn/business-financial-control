from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.v1.deps import get_company_context, get_employee_repository, require_role
from app.application.employee.create_employee import CreateEmployeeUseCase
from app.application.employee.update_employee import UpdateEmployeeUseCase
from app.core.exceptions import NotFoundError
from app.core.tenant import CompanyContext
from app.domain.company.roles import CompanyRole
from app.domain.employee.entities import Employee
from app.domain.employee.repository import EmployeeRepository
from app.schemas.employee import CreateEmployeeRequest, EmployeeResponse, UpdateEmployeeRequest

router = APIRouter(prefix="/companies/{company_id}/employees", tags=["employees"])

_MANAGEMENT_ROLES = (CompanyRole.OWNER, CompanyRole.ADMIN, CompanyRole.MANAGER)


def _to_response(employee: Employee) -> EmployeeResponse:
    return EmployeeResponse(
        id=employee.id,
        company_id=employee.company_id,
        name=employee.name,
        email=employee.email,
        phone=employee.phone,
        role_title=employee.role_title,
        is_active=employee.is_active,
        created_at=employee.created_at,
        updated_at=employee.updated_at,
    )


@router.post("", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
async def create_employee(
    payload: CreateEmployeeRequest,
    company_context: Annotated[CompanyContext, Depends(require_role(*_MANAGEMENT_ROLES))],
    employee_repository: Annotated[EmployeeRepository, Depends(get_employee_repository)],
) -> EmployeeResponse:
    use_case = CreateEmployeeUseCase(employee_repository)
    employee = await use_case.execute(
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        role_title=payload.role_title,
    )
    return _to_response(employee)


@router.get("", response_model=list[EmployeeResponse])
async def list_employees(
    company_context: Annotated[CompanyContext, Depends(get_company_context)],
    employee_repository: Annotated[EmployeeRepository, Depends(get_employee_repository)],
    only_active: Annotated[bool, Query()] = True,
) -> list[EmployeeResponse]:
    employees = await employee_repository.list_all(only_active=only_active)
    return [_to_response(employee) for employee in employees]


@router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee(
    employee_id: str,
    company_context: Annotated[CompanyContext, Depends(get_company_context)],
    employee_repository: Annotated[EmployeeRepository, Depends(get_employee_repository)],
) -> EmployeeResponse:
    employee = await employee_repository.get_by_id(employee_id)
    if employee is None:
        raise NotFoundError("Funcionário não encontrado.")
    return _to_response(employee)


@router.patch("/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: str,
    payload: UpdateEmployeeRequest,
    company_context: Annotated[CompanyContext, Depends(require_role(*_MANAGEMENT_ROLES))],
    employee_repository: Annotated[EmployeeRepository, Depends(get_employee_repository)],
) -> EmployeeResponse:
    use_case = UpdateEmployeeUseCase(employee_repository)
    employee = await use_case.execute(
        employee_id=employee_id, **payload.model_dump(exclude_unset=True)
    )
    return _to_response(employee)
