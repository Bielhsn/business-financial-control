from datetime import datetime

from pydantic import BaseModel


class AccountItemResponse(BaseModel):
    id: str
    description: str
    amount_cents: int
    due_date: datetime | None
    category_id: str
    days_until_due: int | None
    is_overdue: bool


class AccountsBucketResponse(BaseModel):
    overdue_cents: int
    due_soon_cents: int
    upcoming_cents: int
    total_cents: int
    items: list[AccountItemResponse]


class AccountsSummaryResponse(BaseModel):
    payable: AccountsBucketResponse
    receivable: AccountsBucketResponse
