from datetime import datetime

from beanie import Document, Indexed


class SubscriptionDocument(Document):
    company_id: Indexed(str, unique=True)  # type: ignore[valid-type]
    tier: str
    status: str
    billing_cycle: str = "monthly"
    started_at: datetime
    updated_at: datetime
    trial_ends_at: datetime | None = None
    current_period_end: datetime | None = None
    cancel_at_period_end: bool = False

    class Settings:
        name = "subscriptions"
