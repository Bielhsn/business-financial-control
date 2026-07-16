from datetime import UTC, datetime, timedelta

import pytest

from app.application.appointment.change_status import ChangeAppointmentStatusUseCase
from app.application.appointment.create_appointment import CreateAppointmentUseCase
from app.application.appointment.update_appointment import UpdateAppointmentUseCase
from app.core.exceptions import NotFoundError, ValidationError
from app.domain.appointment.entities import AppointmentStatus
from app.domain.catalog.entities import CatalogItemKind
from app.domain.financial.entities import FinancialCategoryType, TransactionStatus
from tests.fakes import (
    FakeAppointmentRepository,
    FakeCatalogItemRepository,
    FakeClientRepository,
    FakeEmployeeRepository,
    FakeFinancialCategoryRepository,
    FakeFinancialTransactionRepository,
)

pytestmark = pytest.mark.anyio

_WHEN = datetime(2026, 8, 1, 14, 0, tzinfo=UTC)


def _create_use_case(
    appointments: FakeAppointmentRepository,
    clients: FakeClientRepository | None = None,
    employees: FakeEmployeeRepository | None = None,
    items: FakeCatalogItemRepository | None = None,
) -> CreateAppointmentUseCase:
    return CreateAppointmentUseCase(
        appointments,
        clients or FakeClientRepository(),
        employees or FakeEmployeeRepository(),
        items or FakeCatalogItemRepository(),
    )


async def test_creates_appointment_with_free_text_title() -> None:
    appointments = FakeAppointmentRepository()
    appointment = await _create_use_case(appointments).execute(
        title="Corte masculino",
        starts_at=_WHEN,
        duration_minutes=30,
        created_by="user-1",
    )

    assert appointment.title == "Corte masculino"
    assert appointment.status == AppointmentStatus.SCHEDULED
    assert appointment.duration_minutes == 30


async def test_service_from_catalog_fills_title_and_price() -> None:
    appointments = FakeAppointmentRepository()
    items = FakeCatalogItemRepository()
    service = await items.create(
        name="Corte + barba",
        description=None,
        price_cents=5000,
        kind=CatalogItemKind.SERVICE,
        tracks_inventory=False,
        stock_quantity=None,
    )

    appointment = await _create_use_case(appointments, items=items).execute(
        starts_at=_WHEN,
        duration_minutes=45,
        catalog_item_id=service.id,
        created_by="user-1",
    )

    assert appointment.title == "Corte + barba"
    assert appointment.price_cents == 5000
    assert appointment.catalog_item_id == service.id


async def test_rejects_non_service_catalog_item() -> None:
    appointments = FakeAppointmentRepository()
    items = FakeCatalogItemRepository()
    product = await items.create(
        name="Pomada",
        description=None,
        price_cents=3000,
        kind=CatalogItemKind.PRODUCT,
        tracks_inventory=False,
        stock_quantity=None,
    )

    with pytest.raises(ValidationError, match="serviços"):
        await _create_use_case(appointments, items=items).execute(
            starts_at=_WHEN,
            duration_minutes=30,
            catalog_item_id=product.id,
            created_by="user-1",
        )


async def test_requires_title_or_service() -> None:
    appointments = FakeAppointmentRepository()
    with pytest.raises(ValidationError, match="título"):
        await _create_use_case(appointments).execute(
            starts_at=_WHEN, duration_minutes=30, created_by="user-1"
        )


async def test_rejects_invalid_duration() -> None:
    appointments = FakeAppointmentRepository()
    with pytest.raises(ValidationError, match="duração"):
        await _create_use_case(appointments).execute(
            title="X", starts_at=_WHEN, duration_minutes=0, created_by="user-1"
        )


async def test_rejects_unknown_client() -> None:
    appointments = FakeAppointmentRepository()
    with pytest.raises(NotFoundError, match="Cliente"):
        await _create_use_case(appointments).execute(
            title="X",
            starts_at=_WHEN,
            duration_minutes=30,
            client_id="missing",
            created_by="user-1",
        )


async def test_list_between_filters_by_window_and_employee() -> None:
    appointments = FakeAppointmentRepository()
    use_case = _create_use_case(appointments)
    await use_case.execute(title="A", starts_at=_WHEN, duration_minutes=30, created_by="u")
    await use_case.execute(
        title="B", starts_at=_WHEN + timedelta(days=10), duration_minutes=30, created_by="u"
    )

    within = await appointments.list_between(
        start=_WHEN - timedelta(hours=1), end=_WHEN + timedelta(days=1)
    )
    assert [a.title for a in within] == ["A"]


async def test_completing_with_price_generates_linked_revenue() -> None:
    appointments = FakeAppointmentRepository()
    clients = FakeClientRepository()
    client = await clients.create(name="João", email=None, phone=None, notes=None, custom_fields={})
    appointment = await _create_use_case(appointments, clients=clients).execute(
        title="Corte",
        starts_at=_WHEN,
        duration_minutes=30,
        client_id=client.id,
        price_cents=4000,
        created_by="user-1",
    )

    categories = FakeFinancialCategoryRepository()
    transactions = FakeFinancialTransactionRepository()
    use_case = ChangeAppointmentStatusUseCase(appointments, categories, transactions)

    updated = await use_case.execute(
        appointment_id=appointment.id,
        status=AppointmentStatus.COMPLETED,
        created_by="user-1",
    )

    assert updated.status == AppointmentStatus.COMPLETED
    assert updated.revenue_transaction_id is not None
    created_transactions = await transactions.list_all()
    assert len(created_transactions) == 1
    transaction = created_transactions[0]
    assert transaction.amount_cents == 4000
    assert transaction.type == FinancialCategoryType.INCOME
    assert transaction.status == TransactionStatus.PAID
    assert transaction.client_id == client.id


async def test_completing_twice_does_not_duplicate_revenue() -> None:
    appointments = FakeAppointmentRepository()
    appointment = await _create_use_case(appointments).execute(
        title="Corte",
        starts_at=_WHEN,
        duration_minutes=30,
        price_cents=4000,
        created_by="user-1",
    )
    categories = FakeFinancialCategoryRepository()
    transactions = FakeFinancialTransactionRepository()
    use_case = ChangeAppointmentStatusUseCase(appointments, categories, transactions)

    await use_case.execute(
        appointment_id=appointment.id, status=AppointmentStatus.COMPLETED, created_by="u"
    )
    await use_case.execute(
        appointment_id=appointment.id, status=AppointmentStatus.COMPLETED, created_by="u"
    )

    assert len(await transactions.list_all()) == 1


async def test_completing_without_price_generates_no_revenue() -> None:
    appointments = FakeAppointmentRepository()
    appointment = await _create_use_case(appointments).execute(
        title="Corte", starts_at=_WHEN, duration_minutes=30, created_by="user-1"
    )
    categories = FakeFinancialCategoryRepository()
    transactions = FakeFinancialTransactionRepository()
    use_case = ChangeAppointmentStatusUseCase(appointments, categories, transactions)

    updated = await use_case.execute(
        appointment_id=appointment.id, status=AppointmentStatus.COMPLETED, created_by="u"
    )

    assert updated.revenue_transaction_id is None
    assert await transactions.list_all() == []


async def test_reschedule_updates_start_and_duration() -> None:
    appointments = FakeAppointmentRepository()
    appointment = await _create_use_case(appointments).execute(
        title="Corte", starts_at=_WHEN, duration_minutes=30, created_by="user-1"
    )
    new_when = _WHEN + timedelta(days=1)

    updated = await UpdateAppointmentUseCase(appointments).execute(
        appointment_id=appointment.id, starts_at=new_when, duration_minutes=60
    )

    assert updated.starts_at == new_when
    assert updated.duration_minutes == 60


async def test_change_status_raises_for_unknown_appointment() -> None:
    use_case = ChangeAppointmentStatusUseCase(
        FakeAppointmentRepository(),
        FakeFinancialCategoryRepository(),
        FakeFinancialTransactionRepository(),
    )
    with pytest.raises(NotFoundError):
        await use_case.execute(
            appointment_id="missing", status=AppointmentStatus.CANCELLED, created_by="u"
        )
