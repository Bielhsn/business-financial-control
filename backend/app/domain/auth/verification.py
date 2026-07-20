import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol


class VerificationPurpose(StrEnum):
    EMAIL_VERIFY = "email_verify"
    PASSWORD_RESET = "password_reset"


def hash_code(code: str, *, secret: str, user_id: str, purpose: "VerificationPurpose") -> str:
    """Hash determinístico (HMAC-SHA256) do código, para poder consultar por hash
    sem guardar o código em texto puro. Determinístico (ao contrário do Argon2)
    porque o código é curto e a busca é por igualdade de hash."""
    message = f"{user_id}:{purpose.value}:{code}".encode()
    return hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()


@dataclass
class VerificationCode:
    id: str
    user_id: str
    purpose: VerificationPurpose
    code_hash: str
    expires_at: datetime
    used: bool
    created_at: datetime


def generate_code() -> str:
    """Código numérico de 6 dígitos, gerado com fonte criptográfica."""
    return f"{secrets.randbelow(1_000_000):06d}"


class VerificationCodeRepository(Protocol):
    async def create(
        self,
        *,
        user_id: str,
        purpose: VerificationPurpose,
        code_hash: str,
        expires_at: datetime,
    ) -> VerificationCode: ...

    async def get_active(
        self, *, user_id: str, purpose: VerificationPurpose, code_hash: str
    ) -> VerificationCode | None:
        """Retorna o código não usado e não expirado que casa com o hash, ou None."""
        ...

    async def mark_used(self, code_id: str) -> None: ...

    async def invalidate_for(self, *, user_id: str, purpose: VerificationPurpose) -> None:
        """Invalida códigos pendentes anteriores (um código ativo por vez)."""
        ...
