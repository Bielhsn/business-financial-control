"""Visão de contas a pagar e a receber a partir dos lançamentos pendentes.

Função pura (testável com primitivos) que classifica cada lançamento pendente em
vencido, a vencer em breve ou futuro, e soma os totais por grupo. Alimenta a tela
de "o que vence essa semana / o que está atrasado" — aproveitando os lançamentos
recorrentes (Etapa 41), que nascem justamente como pendentes com vencimento.
"""

from dataclasses import dataclass, field
from datetime import datetime

from app.domain.financial.entities import (
    FinancialCategoryType,
    FinancialTransaction,
    TransactionStatus,
)
from app.domain.financial.repository import FinancialTransactionRepository

DUE_SOON_DAYS = 7


@dataclass
class AccountItem:
    id: str
    description: str
    amount_cents: int
    due_date: datetime | None
    category_id: str
    days_until_due: int | None  # negativo = vencido; None = sem data de vencimento
    is_overdue: bool


@dataclass
class AccountsBucket:
    overdue_cents: int = 0
    due_soon_cents: int = 0
    upcoming_cents: int = 0
    total_cents: int = 0
    items: list[AccountItem] = field(default_factory=list)


@dataclass
class AccountsSummary:
    payable: AccountsBucket  # a pagar (despesas pendentes)
    receivable: AccountsBucket  # a receber (receitas pendentes)


def compute_accounts(
    transactions: list[FinancialTransaction],
    *,
    today: datetime,
    due_soon_days: int = DUE_SOON_DAYS,
) -> AccountsSummary:
    payable = AccountsBucket()
    receivable = AccountsBucket()

    for transaction in transactions:
        if transaction.status != TransactionStatus.PENDING:
            continue

        days_until_due: int | None = None
        if transaction.due_date is not None:
            days_until_due = (transaction.due_date.date() - today.date()).days

        is_overdue = days_until_due is not None and days_until_due < 0
        bucket = payable if transaction.type == FinancialCategoryType.EXPENSE else receivable

        bucket.total_cents += transaction.amount_cents
        if is_overdue:
            bucket.overdue_cents += transaction.amount_cents
        elif days_until_due is not None and days_until_due <= due_soon_days:
            bucket.due_soon_cents += transaction.amount_cents
        else:
            bucket.upcoming_cents += transaction.amount_cents

        bucket.items.append(
            AccountItem(
                id=transaction.id,
                description=transaction.description,
                amount_cents=transaction.amount_cents,
                due_date=transaction.due_date,
                category_id=transaction.category_id,
                days_until_due=days_until_due,
                is_overdue=is_overdue,
            )
        )

    _sort_items(payable)
    _sort_items(receivable)
    return AccountsSummary(payable=payable, receivable=receivable)


def _sort_items(bucket: AccountsBucket) -> None:
    # Vencidos e vencimentos mais próximos primeiro; sem data por último.
    bucket.items.sort(key=lambda item: (item.due_date is None, item.due_date or datetime.max))


class GetAccountsUseCase:
    """Reúne os lançamentos pendentes da empresa e monta a visão de contas a
    pagar e a receber."""

    def __init__(self, transaction_repository: FinancialTransactionRepository) -> None:
        self._transactions = transaction_repository

    async def execute(self, *, today: datetime) -> AccountsSummary:
        pending = await self._transactions.list_all(status=TransactionStatus.PENDING)
        return compute_accounts(pending, today=today)
