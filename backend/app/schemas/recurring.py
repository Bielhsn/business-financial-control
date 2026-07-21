from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.financial.entities import FinancialCategoryType
from app.domain.recurring.entities import RecurrenceFrequency


class CreateRecurringRequest(BaseModel):
    category_id: str
    type: FinancialCategoryType
    amount_cents: int = Field(gt=0)
    description: str = Field(min_length=1, max_length=200)
    frequency: RecurrenceFrequency
    start_date: datetime
    notes: str | None = Field(default=None, max_length=500)
    client_id: str | None = None


class UpdateRecurringRequest(BaseModel):
    category_id: str | None = None
    type: FinancialCategoryType | None = None
    amount_cents: int | None = Field(default=None, gt=0)
    description: str | None = Field(default=None, min_length=1, max_length=200)
    frequency: RecurrenceFrequency | None = None
    next_run_date: datetime | None = None
    active: bool | None = None
    notes: str | None = Field(default=None, max_length=500)
    client_id: str | None = None


class RecurringResponse(BaseModel):
    id: str
    category_id: str
    type: FinancialCategoryType
    amount_cents: int
    description: str
    frequency: RecurrenceFrequency
    anchor_day: int
    next_run_date: datetime
    active: bool
    notes: str | None
    client_id: str | None
    last_run_at: datetime | None


class GenerateRecurringResponse(BaseModel):
    created: int
