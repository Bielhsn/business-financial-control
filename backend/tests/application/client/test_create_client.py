import pytest

from app.application.client.create_client import CreateClientUseCase
from app.core.exceptions import ValidationError
from app.domain.blueprint.entities import CustomFieldDefinition, CustomFieldType
from tests.fakes import FakeClientRepository, FakeCompanyBlueprintRepository

pytestmark = pytest.mark.anyio


async def test_creates_a_client_without_custom_fields() -> None:
    use_case = CreateClientUseCase(FakeClientRepository(), FakeCompanyBlueprintRepository())

    client = await use_case.execute(
        company_id="company-1",
        name="  Ana Silva  ",
        email="ana@example.com",
        phone="11999999999",
        notes=None,
        custom_fields={},
    )

    assert client.name == "Ana Silva"
    assert client.custom_fields == {}


async def test_rejects_custom_fields_when_no_blueprint_exists() -> None:
    use_case = CreateClientUseCase(FakeClientRepository(), FakeCompanyBlueprintRepository())

    with pytest.raises(ValidationError):
        await use_case.execute(
            company_id="company-1",
            name="Ana",
            email=None,
            phone=None,
            notes=None,
            custom_fields={"favorite_service": "Corte"},
        )


async def test_accepts_custom_fields_defined_in_the_blueprint() -> None:
    blueprint_repository = FakeCompanyBlueprintRepository()
    await blueprint_repository.upsert(
        company_id="company-1",
        modules=["clients"],
        financial_categories=[],
        kpis=[],
        client_custom_fields=[
            CustomFieldDefinition(
                key="favorite_service", label="Serviço favorito", type=CustomFieldType.TEXT
            )
        ],
        ai_provider="anthropic",
    )
    use_case = CreateClientUseCase(FakeClientRepository(), blueprint_repository)

    client = await use_case.execute(
        company_id="company-1",
        name="Ana",
        email=None,
        phone=None,
        notes=None,
        custom_fields={"favorite_service": "Corte"},
    )

    assert client.custom_fields == {"favorite_service": "Corte"}


async def test_rejects_custom_fields_not_defined_in_the_blueprint() -> None:
    blueprint_repository = FakeCompanyBlueprintRepository()
    await blueprint_repository.upsert(
        company_id="company-1",
        modules=["clients"],
        financial_categories=[],
        kpis=[],
        client_custom_fields=[
            CustomFieldDefinition(
                key="favorite_service", label="Serviço favorito", type=CustomFieldType.TEXT
            )
        ],
        ai_provider="anthropic",
    )
    use_case = CreateClientUseCase(FakeClientRepository(), blueprint_repository)

    with pytest.raises(ValidationError):
        await use_case.execute(
            company_id="company-1",
            name="Ana",
            email=None,
            phone=None,
            notes=None,
            custom_fields={"unknown_field": "x"},
        )
