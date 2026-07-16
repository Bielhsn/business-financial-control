from datetime import datetime

from app.core.exceptions import NotFoundError, ValidationError
from app.domain.appointment.entities import Appointment
from app.domain.appointment.repository import AppointmentRepository

_MAX_DURATION_MINUTES = 24 * 60


class UpdateAppointmentUseCase:
    """Reagenda/edita campos do agendamento. Não altera status nem a receita
    gerada — mudança de status passa por `ChangeAppointmentStatusUseCase`."""

    def __init__(self, appointment_repository: AppointmentRepository) -> None:
        self._appointment_repository = appointment_repository

    async def execute(
        self,
        *,
        appointment_id: str,
        starts_at: datetime | None = None,
        duration_minutes: int | None = None,
        title: str | None = None,
        notes: str | None = None,
        price_cents: int | None = None,
    ) -> Appointment:
        fields: dict[str, object] = {}
        if starts_at is not None:
            fields["starts_at"] = starts_at
        if duration_minutes is not None:
            if duration_minutes <= 0 or duration_minutes > _MAX_DURATION_MINUTES:
                raise ValidationError("A duração deve estar entre 1 minuto e 24 horas.")
            fields["duration_minutes"] = duration_minutes
        if title is not None:
            clean_title = title.strip()
            if not clean_title:
                raise ValidationError("O título não pode ficar vazio.")
            fields["title"] = clean_title
        if notes is not None:
            fields["notes"] = notes.strip() or None
        if price_cents is not None:
            if price_cents < 0:
                raise ValidationError("O preço não pode ser negativo.")
            fields["price_cents"] = price_cents

        if not fields:
            appointment = await self._appointment_repository.get_by_id(appointment_id)
            if appointment is None:
                raise NotFoundError("Agendamento não encontrado.")
            return appointment

        appointment = await self._appointment_repository.update(appointment_id, **fields)
        if appointment is None:
            raise NotFoundError("Agendamento não encontrado.")
        return appointment
