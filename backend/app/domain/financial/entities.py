from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class FinancialCategoryType(StrEnum):
    INCOME = "income"
    EXPENSE = "expense"


class TransactionStatus(StrEnum):
    PENDING = "pending"
    PAID = "paid"
    CANCELLED = "cancelled"


@dataclass
class FinancialCategory:
    id: str
    company_id: str
    name: str
    type: FinancialCategoryType
    is_active: bool
    created_at: datetime


@dataclass
class FinancialTransaction:
    """Lançamento financeiro. amount_cents é o valor na menor unidade da moeda
    (ex.: centavos), como na API do Stripe — evita erros de arredondamento de
    ponto flutuante e problemas de serialização de Decimal no MongoDB."""

    id: str
    company_id: str
    category_id: str
    type: FinancialCategoryType
    amount_cents: int
    description: str
    status: TransactionStatus
    due_date: datetime | None
    paid_at: datetime | None
    notes: str | None
    client_id: str | None
    created_by: str
    created_at: datetime
    updated_at: datetime
    # Referência externa (ex.: "hotmart:HP123") quando o lançamento veio de uma
    # integração — garante idempotência do sync (não duplica na re-sincronização).
    external_ref: str | None = None


@dataclass
class CashFlowSummary:
    start: datetime
    end: datetime
    income_cents: int
    expense_cents: int
    balance_cents: int
