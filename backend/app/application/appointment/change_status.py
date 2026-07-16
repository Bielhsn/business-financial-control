from datetime import UTC, datetime

from app.core.exceptions import NotFoundError
from app.domain.appointment.entities import Appointment, AppointmentStatus
from app.domain.appointment.repository import AppointmentRepository
from app.domain.financial.entities import FinancialCategoryType, TransactionStatus
from app.domain.financial.repository import (
    FinancialCategoryRepository,
    FinancialTransactionRepository,
)

# Categoria onde as receitas de atendimentos concluídos são lançadas.
_REVENUE_CATEGORY_NAME = "Atendimentos"


class ChangeAppointmentStatusUseCase:
    """Muda o status do agendamento. Ao concluir com preço e cliente, gera um
    lançamento de receita PAID vinculado ao cliente — de forma idempotente
    (concluir de novo não duplica a receita)."""

    def __init__(
        self,
        appointment_repository: AppointmentRepository,
        category_repository: FinancialCategoryRepository,
        transaction_repository: FinancialTransactionRepository,
    ) -> None:
        self._appointment_repository = appointment_repository
        self._category_repository = category_repository
        self._transaction_repository = transaction_repository

    async def execute(
        self, *, appointment_id: str, status: AppointmentStatus, created_by: str
    ) -> Appointment:
        appointment = await self._appointment_repository.get_by_id(appointment_id)
        if appointment is None:
            raise NotFoundError("Agendamento não encontrado.")

        fields: dict[str, object] = {"status": status.value}

        if (
            status == AppointmentStatus.COMPLETED
            and appointment.revenue_transaction_id is None
            and appointment.price_cents is not None
            and appointment.price_cents > 0
        ):
            transaction_id = await self._generate_revenue(appointment, created_by)
            fields["revenue_transaction_id"] = transaction_id

        updated = await self._appointment_repository.update(appointment_id, **fields)
        if updated is None:
            raise NotFoundError("Agendamento não encontrado.")
        return updated

    async def _generate_revenue(self, appointment: Appointment, created_by: str) -> str:
        category = await self._category_repository.get_by_name_and_type(
            _REVENUE_CATEGORY_NAME, FinancialCategoryType.INCOME
        )
        if category is None:
            category = await self._category_repository.create(
                name=_REVENUE_CATEGORY_NAME, type=FinancialCategoryType.INCOME
            )
        assert appointment.price_cents is not None
        transaction = await self._transaction_repository.create(
            category_id=category.id,
            type=FinancialCategoryType.INCOME,
            amount_cents=appointment.price_cents,
            description=appointment.title,
            status=TransactionStatus.PAID,
            due_date=None,
            paid_at=datetime.now(UTC),
            notes=None,
            client_id=appointment.client_id,
            created_by=created_by,
        )
        return transaction.id
