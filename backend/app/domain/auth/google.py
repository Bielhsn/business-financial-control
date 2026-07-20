from dataclasses import dataclass
from typing import Protocol


@dataclass
class GoogleIdentity:
    email: str
    full_name: str
    email_verified: bool


class GoogleTokenVerifier(Protocol):
    async def verify(self, id_token: str) -> GoogleIdentity:
        """Valida o id_token do Google e retorna a identidade. Levanta
        UnauthorizedError se o token for inválido/expirado/de outra audiência."""
        ...
