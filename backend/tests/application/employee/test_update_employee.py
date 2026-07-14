import pytest

from app.application.employee.create_employee import CreateEmployeeUseCase
from app.application.employee.update_employee import UpdateEmployeeUseCase
from app.core.exceptions import NotFoundError
from tests.fakes import FakeEmployeeRepository


@pytest.mark.anyio
async def test_updates_only_the_provided_fields() -> None:
    repository = FakeEmployeeRepository()
    employee = await CreateEmployeeUseCase(repository).execute(
        name="João", email=None, phone=None, role_title="Barbeiro"
    )

    updated = await UpdateEmployeeUseCase(repository).execute(
        employee_id=employee.id, is_active=False
    )

    assert updated.is_active is False
    assert updated.role_title == "Barbeiro"


@pytest.mark.anyio
async def test_raises_not_found_for_unknown_employee() -> None:
    with pytest.raises(NotFoundError):
        await UpdateEmployeeUseCase(FakeEmployeeRepository()).execute(
            employee_id="does-not-exist", name="X"
        )


@pytest.mark.anyio
async def test_returns_employee_unchanged_when_no_fields_are_provided() -> None:
    repository = FakeEmployeeRepository()
    employee = await CreateEmployeeUseCase(repository).execute(
        name="João", email=None, phone=None, role_title="Barbeiro"
    )

    result = await UpdateEmployeeUseCase(repository).execute(employee_id=employee.id)

    assert result.name == "João"


@pytest.mark.anyio
async def test_raises_not_found_when_no_fields_are_provided_for_unknown_employee() -> None:
    with pytest.raises(NotFoundError):
        await UpdateEmployeeUseCase(FakeEmployeeRepository()).execute(employee_id="does-not-exist")
