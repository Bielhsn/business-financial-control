from datetime import datetime

from pydantic import BaseModel

from app.application.notifications.get_notifications import NotificationKind
from app.domain.financial.entities import FinancialCategoryType


class NotificationResponse(BaseModel):
    kind: NotificationKind
    transaction_id: str
    description: str
    amount_cents: int
    type: FinancialCategoryType
    due_date: datetime
