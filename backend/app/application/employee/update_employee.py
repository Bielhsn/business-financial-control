from app.core.exceptions import NotFoundError
from app.domain.employee.entities import Employee
from app.domain.employee.repository import EmployeeRepository


class UpdateEmployeeUseCase:
    def __init__(self, employee_repository: EmployeeRepository) -> None:
        self._employee_repository = employee_repository

    async def execute(self, *, employee_id: str, **fields: object) -> Employee:
        clean_fields = {key: value for key, value in fields.items() if value is not None}
        if not clean_fields:
            employee = await self._employee_repository.get_by_id(employee_id)
            if employee is None:
                raise NotFoundError("Funcionário não encontrado.")
            return employee

        employee = await self._employee_repository.update(employee_id, **clean_fields)
        if employee is None:
            raise NotFoundError("Funcionário não encontrado.")
        return employee
