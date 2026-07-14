import pytest

from app.application.client.create_client import CreateClientUseCase
from app.application.client.update_client import UpdateClientUseCase
from app.core.exceptions import NotFoundError, ValidationError
from tests.fakes import FakeClientRepository, FakeCompanyBlueprintRepository

pytestmark = pytest.mark.anyio


async def test_updates_only_the_provided_fields() -> None:
    client_repository = FakeClientRepository()
    blueprint_repository = FakeCompanyBlueprintRepository()
    client = await CreateClientUseCase(client_repository, blueprint_repository).execute(
        company_id="company-1",
        name="Ana",
        email=None,
        phone=None,
        notes=None,
        custom_fields={},
    )

    updated = await UpdateClientUseCase(client_repository, blueprint_repository).execute(
        company_id="company-1", client_id=client.id, name="Ana Silva"
    )

    assert updated.name == "Ana Silva"


async def test_validates_custom_fields_on_update() -> None:
    client_repository = FakeClientRepository()
    blueprint_repository = FakeCompanyBlueprintRepository()
    client = await CreateClientUseCase(client_repository, blueprint_repository).execute(
        company_id="company-1",
        name="Ana",
        email=None,
        phone=None,
        notes=None,
        custom_fields={},
    )

    with pytest.raises(ValidationError):
        await UpdateClientUseCase(client_repository, blueprint_repository).execute(
            company_id="company-1",
            client_id=client.id,
            custom_fields={"unknown_field": "x"},
        )


async def test_raises_not_found_for_unknown_client() -> None:
    with pytest.raises(NotFoundError):
        await UpdateClientUseCase(FakeClientRepository(), FakeCompanyBlueprintRepository()).execute(
            company_id="company-1", client_id="does-not-exist", name="X"
        )


async def test_returns_client_unchanged_when_no_fields_are_provided() -> None:
    client_repository = FakeClientRepository()
    blueprint_repository = FakeCompanyBlueprintRepository()
    client = await CreateClientUseCase(client_repository, blueprint_repository).execute(
        company_id="company-1",
        name="Ana",
        email=None,
        phone=None,
        notes=None,
        custom_fields={},
    )

    result = await UpdateClientUseCase(client_repository, blueprint_repository).execute(
        company_id="company-1", client_id=client.id
    )

    assert result.name == "Ana"


async def test_raises_not_found_when_no_fields_are_provided_for_unknown_client() -> None:
    with pytest.raises(NotFoundError):
        await UpdateClientUseCase(FakeClientRepository(), FakeCompanyBlueprintRepository()).execute(
            company_id="company-1", client_id="does-not-exist"
        )
