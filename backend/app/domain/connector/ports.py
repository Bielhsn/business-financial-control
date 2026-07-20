from datetime import datetime
from typing import Protocol

from app.domain.connector.entities import NormalizedSale


class SecretCipher(Protocol):
    """Criptografia simétrica dos segredos de integração em repouso."""

    def encrypt(self, plaintext: str) -> str: ...

    def decrypt(self, token: str) -> str: ...


class Connector(Protocol):
    """Contrato que todo conector de provedor externo implementa.

    Manter esta interface pequena é o que torna a arquitetura modular: um novo
    provedor = uma nova classe que implementa `test_connection` + `fetch_sales`,
    registrada no `CONNECTOR_REGISTRY` e no factory. Nada no motor de sync, na
    API ou no frontend precisa mudar."""

    provider: str

    async def test_connection(self, credentials: dict[str, str]) -> None:
        """Valida as credenciais (autentica no provedor). Levanta ConnectorError
        se forem inválidas."""
        ...

    async def fetch_sales(
        self, credentials: dict[str, str], *, since: datetime | None
    ) -> list[NormalizedSale]:
        """Busca vendas/reembolsos desde `since` (ou tudo, se None)."""
        ...
