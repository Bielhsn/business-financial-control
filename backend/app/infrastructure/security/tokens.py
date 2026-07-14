import secrets
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from typing import Any

import jwt

from app.core.config import Settings
from app.core.exceptions import UnauthorizedError

_ALGORITHM = "HS256"


class JWTTokenService:
    """Access tokens JWT de curta duração; refresh tokens opacos e revogáveis."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def create_access_token(self, subject: str) -> str:
        now = datetime.now(UTC)
        payload = {
            "sub": subject,
            "iat": now,
            "exp": now + timedelta(minutes=self._settings.access_token_expire_minutes),
        }
        return jwt.encode(payload, self._settings.secret_key, algorithm=_ALGORITHM)

    def decode_access_token(self, token: str) -> dict[str, Any]:
        try:
            return jwt.decode(token, self._settings.secret_key, algorithms=[_ALGORITHM])
        except jwt.PyJWTError as exc:
            raise UnauthorizedError("Token inválido ou expirado.") from exc

    def generate_refresh_token(self) -> str:
        return secrets.token_urlsafe(64)

    def hash_refresh_token(self, raw_token: str) -> str:
        return sha256(raw_token.encode("utf-8")).hexdigest()
