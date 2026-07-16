from datetime import datetime

from app.core.exceptions import NotFoundError, ValidationError
from app.domain.appointment.entities import Appointment
from app.domain.appointment.repository import AppointmentRepository
from app.domain.catalog.entities import CatalogItemKind
from app.domain.catalog.repository import CatalogItemRepository
from app.domain.client.repository import ClientRepository
from app.domain.employee.repository import EmployeeRepository

_MAX_DURATION_MINUTES = 24 * 60


class CreateAppointmentUseCase:
    """Cria um agendamento reaproveitando os cadastros existentes (cliente,
    funcionário, serviço do catálogo) quando informados, sem duplicá-los."""

    def __init__(
        self,
        appointment_repository: AppointmentRepository,
        client_repository: ClientRepository,
        employee_repository: EmployeeRepository,
        catalog_item_repository: CatalogItemRepository,
    ) -> None:
        self._appointment_repository = appointment_repository
        self._client_repository = client_repository
        self._employee_repository = employee_repository
        self._catalog_item_repository = catalog_item_repository

    async def execute(
        self,
        *,
        starts_at: datetime,
        duration_minutes: int,
        created_by: str,
        title: str | None = None,
        client_id: str | None = None,
        employee_id: str | None = None,
        catalog_item_id: str | None = None,
        price_cents: int | None = None,
        notes: str | None = None,
    ) -> Appointment:
        if duration_minutes <= 0 or duration_minutes > _MAX_DURATION_MINUTES:
            raise ValidationError("A duração deve estar entre 1 minuto e 24 horas.")
        if price_cents is not None and price_cents < 0:
            raise ValidationError("O preço não pode ser negativo.")

        client_name: str | None = None
        if client_id is not None:
            client = await self._client_repository.get_by_id(client_id)
            if client is None:
                raise NotFoundError("Cliente não encontrado.")
            client_name = client.name

        employee_name: str | None = None
        if employee_id is not None:
            employee = await self._employee_repository.get_by_id(employee_id)
            if employee is None:
                raise NotFoundError("Funcionário não encontrado.")
            employee_name = employee.name

        resolved_title = title.strip() if title else None
        if catalog_item_id is not None:
            item = await self._catalog_item_repository.get_by_id(catalog_item_id)
            if item is None:
                raise NotFoundError("Serviço não encontrado no catálogo.")
            if item.kind != CatalogItemKind.SERVICE:
                raise ValidationError("Apenas serviços do catálogo podem ser agendados.")
            if not resolved_title:
                resolved_title = item.name
            if price_cents is None:
                price_cents = item.promo_price_cents or item.price_cents

        if not resolved_title:
            raise ValidationError("Informe um título ou selecione um serviço do catálogo.")

        return await self._appointment_repository.create(
            title=resolved_title,
            starts_at=starts_at,
            duration_minutes=duration_minutes,
            client_id=client_id,
            client_name=client_name,
            employee_id=employee_id,
            employee_name=employee_name,
            catalog_item_id=catalog_item_id,
            price_cents=price_cents,
            notes=notes.strip() if notes else None,
            created_by=created_by,
        )
