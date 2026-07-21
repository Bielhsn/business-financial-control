import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

_PREFIX = "aur_"
_DISPLAY_LEN = 12  # "aur_" + 8 chars mostrados na listagem


@dataclass
class ApiKey:
    """Chave de API de uma empresa. O segredo em si nunca é guardado — só o hash
    (para consulta) e um prefixo curto (para identificação na tela)."""

    id: str
    company_id: str
    name: str
    prefix: str  # ex.: "aur_ab12cd34" (não é segredo)
    created_at: datetime
    last_used_at: datetime | None
    revoked: bool


def generate_api_key() -> str:
    """Gera a chave crua (mostrada uma única vez ao usuário)."""
    return _PREFIX + secrets.token_urlsafe(24)


def api_key_prefix(raw_key: str) -> str:
    return raw_key[:_DISPLAY_LEN]


def hash_api_key(raw_key: str, *, secret: str) -> str:
    """Hash determinístico (HMAC-SHA256) para consulta por igualdade, sem guardar
    a chave em texto puro."""
    return hmac.new(secret.encode(), raw_key.encode(), hashlib.sha256).hexdigest()


class ApiKeyRepository(Protocol):
    async def create(self, *, name: str, prefix: str, hashed_key: str) -> ApiKey:
        """Cria a chave na empresa do contexto atual (tenant)."""
        ...

    async def list_for_company(self) -> list[ApiKey]:
        """Chaves da empresa do contexto atual."""
        ...

    async def get_active_by_hash(self, hashed_key: str) -> ApiKey | None:
        """Consulta CROSS-TENANT por hash (a requisição só traz a chave). Retorna
        a chave não revogada correspondente, ou None."""
        ...

    async def revoke(self, key_id: str) -> bool:
        """Revoga uma chave da empresa do contexto atual."""
        ...

    async def touch_last_used(self, key_id: str) -> None: ...
