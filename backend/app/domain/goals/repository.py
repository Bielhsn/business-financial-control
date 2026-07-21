from typing import Protocol

from app.domain.goals.entities import FinancialGoal, GoalMetric


class GoalRepository(Protocol):
    """Metas escopadas por empresa (tenant). Uma meta por métrica, no máximo."""

    async def list_all(self) -> list[FinancialGoal]: ...

    async def set(self, *, metric: GoalMetric, target_cents: int) -> FinancialGoal:
        """Cria ou atualiza a meta da métrica (upsert)."""
        ...

    async def delete(self, metric: GoalMetric) -> bool: ...
