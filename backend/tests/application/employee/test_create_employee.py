import pytest

from app.application.employee.create_employee import CreateEmployeeUseCase
from tests.fakes import FakeEmployeeRepository

pytestmark = pytest.mark.anyio


async def test_creates_an_employee_with_normalized_fields() -> None:
    employee = await CreateEmployeeUseCase(FakeEmployeeRepository()).execute(
        name="  João  ", email="joao@example.com", phone=None, role_title="  Barbeiro  "
    )

    assert employee.name == "João"
    assert employee.role_title == "Barbeiro"
    assert employee.is_active is True
