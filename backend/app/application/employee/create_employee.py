from app.domain.employee.entities import Employee
from app.domain.employee.repository import EmployeeRepository


class CreateEmployeeUseCase:
    def __init__(self, employee_repository: EmployeeRepository) -> None:
        self._employee_repository = employee_repository

    async def execute(
        self,
        *,
        name: str,
        email: str | None,
        phone: str | None,
        role_title: str | None,
    ) -> Employee:
        return await self._employee_repository.create(
            name=name.strip(),
            email=email,
            phone=phone,
            role_title=role_title.strip() if role_title else None,
        )
