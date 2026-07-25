from dataclasses import dataclass
from datetime import datetime


@dataclass
class Client:
    id: str
    company_id: str
    name: str
    email: str | None
    phone: str | None
    notes: str | None
    custom_fields: dict[str, str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    # Retorno de clientes (ex.: barbearia): a cada quantos dias esperar o cliente
    # de volta e quando foi o último atendimento — usados para sinalizar quem já
    # está "na hora de voltar" e disparar o convite por WhatsApp.
    return_interval_days: int | None = None
    last_visit_at: datetime | None = None


@dataclass
class ClientSummary:
    client_id: str
    total_spent_cents: int
    purchase_count: int
    last_purchase_at: datetime | None
