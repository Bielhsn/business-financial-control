from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.financial.entities import FinancialCategoryType, TransactionStatus


class CreateCategoryRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    type: FinancialCategoryType


class UpdateCategoryRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    is_active: bool | None = None


class FinancialCategoryResponse(BaseModel):
    id: str
    company_id: str
    name: str
    type: FinancialCategoryType
    is_active: bool
    created_at: datetime


class CreateTransactionRequest(BaseModel):
    category_id: str
    type: FinancialCategoryType
    amount_cents: int = Field(gt=0)
    description: str = Field(min_length=1, max_length=500)
    due_date: datetime | None = None
    paid_at: datetime | None = None
    notes: str | None = Field(default=None, max_length=2000)


class UpdateTransactionRequest(BaseModel):
    amount_cents: int | None = Field(default=None, gt=0)
    description: str | None = Field(default=None, min_length=1, max_length=500)
    due_date: datetime | None = None
    notes: str | None = Field(default=None, max_length=2000)


class MarkPaidRequest(BaseModel):
    paid_at: datetime | None = None


class FinancialTransactionResponse(BaseModel):
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
    created_by: str
    created_at: datetime
    updated_at: datetime


class CashFlowSummaryResponse(BaseModel):
    start: datetime
    end: datetime
    income_cents: int
    expense_cents: int
    balance_cents: int
