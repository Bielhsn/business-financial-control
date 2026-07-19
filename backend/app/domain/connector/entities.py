from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class ConnectionStatus(StrEnum):
    CONNECTED = "connected"
    ERROR = "error"


@dataclass
class Connection:
    """Uma conexão de uma empresa com um provedor externo (ex.: Hotmart).

    Os segredos (tokens/chaves) nunca vivem nesta entidade — ficam
    criptografados no repositório e só são descriptografados no momento do
    sync. `config` guarda apenas dados não sensíveis (ex.: id da conta)."""

    id: str
    company_id: str
    provider: str
    status: ConnectionStatus
    config: dict[str, str]
    last_synced_at: datetime | None
    last_error: str | None
    created_at: datetime
    updated_at: datetime


@dataclass
class NormalizedSale:
    """Venda/reembolso normalizado, independente do provedor de origem.

    Cada conector traduz o formato da sua API para esta forma comum; o motor de
    sync sabe apenas lidar com `NormalizedSale`, então adicionar um provedor não
    muda o motor."""

    external_id: str
    description: str
    amount_cents: int
    occurred_at: datetime
    is_refund: bool = False
    buyer_name: str | None = None
    buyer_email: str | None = None


@dataclass
class SyncResult:
    imported: int = 0
    skipped: int = 0
    details: dict[str, int] = field(default_factory=dict)
