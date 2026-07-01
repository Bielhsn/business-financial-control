from typing import Protocol

from app.domain.employee.entities import Employee


class EmployeeRepository(Protocol):
    """Toda implementação filtra/carimba pela empresa do contexto de tenant atual."""

    async def create(
        self, *, name: str, email: str | None, phone: str | None, role_title: str | None
    ) -> Employee: ...

    async def get_by_id(self, employee_id: str) -> Employee | None: ...

    async def list_all(self, *, only_active: bool = True) -> list[Employee]: ...

    async def update(self, employee_id: str, **fields: object) -> Employee | None: ...
