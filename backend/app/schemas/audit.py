from datetime import datetime

from pydantic import BaseModel


class AuditEntryResponse(BaseModel):
    id: str
    user_id: str | None
    action: str
    details: dict[str, object]
    created_at: datetime | None
