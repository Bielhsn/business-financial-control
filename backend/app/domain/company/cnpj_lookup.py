from dataclasses import dataclass
from typing import Protocol


@dataclass
class CnpjInfo:
    """Dados públicos de um CNPJ, normalizados a partir da fonte externa."""

    cnpj: str
    legal_name: str | None
    trade_name: str | None
    status: str | None  # situação cadastral (ex.: "ATIVA")
    is_active: bool
    city: str | None
    state: str | None
    email: str | None
    phone: str | None
    main_activity: str | None


class CnpjLookup(Protocol):
    """Consulta dados públicos de um CNPJ numa fonte externa (ex.: BrasilAPI)."""

    async def fetch(self, cnpj: str) -> CnpjInfo:
        """`cnpj` já normalizado (14 dígitos). Levanta NotFoundError se não existir
        e ConnectorError em falha da fonte."""
        ...
