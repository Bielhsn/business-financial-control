from dataclasses import dataclass
from datetime import datetime


@dataclass
class RefreshToken:
    id: str
    user_id: str
    token_hash: str
    expires_at: datetime
    revoked: bool
    created_at: datetime
