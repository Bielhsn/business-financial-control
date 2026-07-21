from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from app.domain.financial.entities import FinancialCategoryType


class RecurrenceFrequency(StrEnum):
    """Periodicidade de um lançamento recorrente."""

    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


@dataclass
class RecurringTransaction:
    """Modelo de um lançamento que se repete (ex.: aluguel, salários, assinaturas).

    Não é um lançamento financeiro em si — é a "regra". A cada período devido, o
    motor de geração materializa um `FinancialTransaction` real (pendente, com
    vencimento na data), de forma idempotente. `anchor_day` guarda o dia do mês
    original para que "todo dia 31" não vire "dia 28" permanentemente."""

    id: str
    company_id: str
    category_id: str
    type: FinancialCategoryType
    amount_cents: int
    description: str
    frequency: RecurrenceFrequency
    anchor_day: int
    next_run_date: datetime
    active: bool
    notes: str | None
    client_id: str | None
    created_by: str
    created_at: datetime
    updated_at: datetime
    last_run_at: datetime | None = None
