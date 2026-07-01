from datetime import datetime

from app.domain.financial.entities import CashFlowSummary, FinancialCategoryType
from app.domain.financial.repository import FinancialTransactionRepository


class GetCashFlowSummaryUseCase:
    def __init__(self, transaction_repository: FinancialTransactionRepository) -> None:
        self._transaction_repository = transaction_repository

    async def execute(self, *, start: datetime, end: datetime) -> CashFlowSummary:
        income_cents = await self._transaction_repository.sum_paid_between(
            type=FinancialCategoryType.INCOME, start=start, end=end
        )
        expense_cents = await self._transaction_repository.sum_paid_between(
            type=FinancialCategoryType.EXPENSE, start=start, end=end
        )
        return CashFlowSummary(
            start=start,
            end=end,
            income_cents=income_cents,
            expense_cents=expense_cents,
            balance_cents=income_cents - expense_cents,
        )
