from datetime import UTC, datetime

from app.core.tenant import get_current_company_id
from app.domain.goals.entities import FinancialGoal, GoalMetric
from app.infrastructure.database.models.goal import GoalDocument


def _to_entity(document: GoalDocument) -> FinancialGoal:
    return FinancialGoal(
        id=str(document.id),
        company_id=document.company_id,
        metric=GoalMetric(document.metric),
        target_cents=document.target_cents,
        updated_at=document.updated_at,
    )


class BeanieGoalRepository:
    """Escopado por empresa (tenant) via contexto atual."""

    async def list_all(self) -> list[FinancialGoal]:
        company_id = get_current_company_id()
        documents = await GoalDocument.find(GoalDocument.company_id == company_id).to_list()
        return [_to_entity(document) for document in documents]

    async def set(self, *, metric: GoalMetric, target_cents: int) -> FinancialGoal:
        company_id = get_current_company_id()
        now = datetime.now(UTC)
        document = await GoalDocument.find_one(
            GoalDocument.company_id == company_id,
            GoalDocument.metric == metric.value,
        )
        if document is None:
            document = GoalDocument(
                company_id=company_id,
                metric=metric.value,
                target_cents=target_cents,
                updated_at=now,
            )
            await document.insert()
        else:
            document.target_cents = target_cents
            document.updated_at = now
            await document.save()
        return _to_entity(document)

    async def delete(self, metric: GoalMetric) -> bool:
        company_id = get_current_company_id()
        document = await GoalDocument.find_one(
            GoalDocument.company_id == company_id,
            GoalDocument.metric == metric.value,
        )
        if document is None:
            return False
        await document.delete()
        return True
