from typing import Protocol

from app.domain.admin.metrics import CompanySummary, ConnectionSummary, FinancialTotals


class AdminMetricsRepository(Protocol):
    """Consultas de leitura que cruzam todos os tenants — exclusivas do painel
    administrativo. Implementações devem ignorar o escopo de empresa."""

    async def list_companies(self) -> list[CompanySummary]: ...

    async def count_users(self) -> int: ...

    async def list_connections(self) -> list[ConnectionSummary]: ...

    async def financial_totals(self) -> FinancialTotals: ...
