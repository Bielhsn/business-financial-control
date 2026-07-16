from datetime import datetime
from typing import Protocol

from app.domain.appointment.entities import Appointment, AppointmentStatus


class AppointmentRepository(Protocol):
    """Toda implementação filtra/carimba pela empresa do contexto de tenant atual
    (`core.tenant.get_current_company_id()`) — o chamador nunca informa `company_id`."""

    async def create(
        self,
        *,
        title: str,
        starts_at: datetime,
        duration_minutes: int,
        client_id: str | None,
        client_name: str | None,
        employee_id: str | None,
        employee_name: str | None,
        catalog_item_id: str | None,
        price_cents: int | None,
        notes: str | None,
        created_by: str,
    ) -> Appointment: ...

    async def get_by_id(self, appointment_id: str) -> Appointment | None: ...

    async def list_between(
        self,
        *,
        start: datetime,
        end: datetime,
        employee_id: str | None = None,
    ) -> list[Appointment]: ...

    async def update(self, appointment_id: str, **fields: object) -> Appointment | None: ...


# Reexport para conveniência dos chamadores.
__all__ = ["AppointmentRepository", "AppointmentStatus"]
