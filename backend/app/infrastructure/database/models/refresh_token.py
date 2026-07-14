from datetime import datetime

from beanie import Document, Indexed


class RefreshTokenDocument(Document):
    user_id: str
    token_hash: Indexed(str, unique=True)  # type: ignore[valid-type]
    expires_at: datetime
    revoked: bool = False
    created_at: datetime

    class Settings:
        name = "refresh_tokens"
