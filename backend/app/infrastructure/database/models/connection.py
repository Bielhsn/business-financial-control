from datetime import datetime

from beanie import Document, Indexed
from pymongo import IndexModel


class ConnectionDocument(Document):
    company_id: Indexed(str)  # type: ignore[valid-type]
    provider: str
    status: str = "connected"
    # Segredos criptografados (string opaca Fernet) — nunca em texto puro.
    encrypted_secrets: str
    config: dict[str, str] = {}
    last_synced_at: datetime | None = None
    last_error: str | None = None
    created_at: datetime
    updated_at: datetime

    class Settings:
        name = "connections"
        indexes = [
            # Uma conexão por empresa+provedor.
            IndexModel([("company_id", 1), ("provider", 1)], unique=True),
        ]
