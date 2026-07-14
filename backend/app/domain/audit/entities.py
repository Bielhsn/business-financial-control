from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class AuditEntry:
    id: str
    company_id: str
    user_id: str | None
    action: str
    details: dict[str, object] = field(default_factory=dict)
    created_at: datetime | None = None
