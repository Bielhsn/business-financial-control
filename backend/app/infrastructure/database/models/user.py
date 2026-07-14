from datetime import datetime

from beanie import Document, Indexed
from pydantic import EmailStr


class UserDocument(Document):
    email: Indexed(EmailStr, unique=True)  # type: ignore[valid-type]
    hashed_password: str
    full_name: str
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Settings:
        name = "users"
