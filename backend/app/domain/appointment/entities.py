from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class AppointmentStatus(StrEnum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


@dataclass
class Appointment:
    """Um agendamento na agenda da empresa.

    `client_id`, `employee_id` e `catalog_item_id` são referências opcionais aos
    módulos já existentes (clientes, funcionários, catálogo de serviços) — a
    agenda reaproveita esses cadastros em vez de duplicá-los, mas também aceita
    apenas o nome digitado, para quem ainda não cadastrou nada.

    Quando um agendamento é concluído com preço, um lançamento de receita é gerado
    e seu id fica em `revenue_transaction_id`, garantindo idempotência (concluir
    de novo não duplica a receita)."""

    id: str
    company_id: str
    title: str
    starts_at: datetime
    duration_minutes: int
    status: AppointmentStatus
    client_id: str | None
    client_name: str | None
    employee_id: str | None
    employee_name: str | None
    catalog_item_id: str | None
    price_cents: int | None
    notes: str | None
    revenue_transaction_id: str | None
    created_by: str
    created_at: datetime
    updated_at: datetime
