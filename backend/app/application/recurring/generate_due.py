"""Materializa as recorrências vencidas em lançamentos financeiros reais.

Cada ocorrência vira um `FinancialTransaction` **pendente** com vencimento na
data — alimentando contas a pagar/receber, fluxo de caixa e previsão. A geração
é idempotente por `external_ref` (`recurring:<id>:<data>`), então rodar duas
vezes não duplica; e faz "catch-up" de períodos perdidos (com um teto de
segurança) caso ninguém rode a geração por um tempo."""

from dataclasses import dataclass
from datetime import datetime

from app.domain.financial.entities import TransactionStatus
from app.domain.financial.repository import FinancialTransactionRepository
from app.domain.recurring.repository import RecurringTransactionRepository
from app.domain.recurring.schedule import next_occurrence

# Teto de ocorrências geradas por recorrência numa única execução — evita um laço
# descontrolado se uma data-base ficar muito no passado.
_MAX_CATCHUP = 120


@dataclass
class GenerateResult:
    created: int = 0


class GenerateDueRecurringUseCase:
    def __init__(
        self,
        recurring_repository: RecurringTransactionRepository,
        transaction_repository: FinancialTransactionRepository,
    ) -> None:
        self._recurring = recurring_repository
        self._transactions = transaction_repository

    async def execute(self, *, as_of: datetime, created_by: str) -> GenerateResult:
        due = await self._recurring.list_due(as_of)
        result = GenerateResult()

        for item in due:
            occurrence = item.next_run_date
            last_run = item.last_run_at
            for _ in range(_MAX_CATCHUP):
                if occurrence > as_of:
                    break
                external_ref = f"recurring:{item.id}:{occurrence.date().isoformat()}"
                existing = await self._transactions.find_by_external_ref(external_ref)
                if existing is None:
                    await self._transactions.create(
                        category_id=item.category_id,
                        type=item.type,
                        amount_cents=item.amount_cents,
                        description=item.description,
                        status=TransactionStatus.PENDING,
                        due_date=occurrence,
                        paid_at=None,
                        notes=item.notes,
                        client_id=item.client_id,
                        created_by=created_by,
                        external_ref=external_ref,
                    )
                    result.created += 1
                last_run = occurrence
                occurrence = next_occurrence(occurrence, item.frequency, anchor_day=item.anchor_day)

            await self._recurring.update(item.id, next_run_date=occurrence, last_run_at=last_run)

        return result
