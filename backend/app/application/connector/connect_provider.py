import json

from app.core.exceptions import ValidationError
from app.domain.connector.entities import Connection
from app.domain.connector.ports import Connector, SecretCipher
from app.domain.connector.registry import get_connector_definition
from app.domain.connector.repository import ConnectionRepository


def split_credentials(
    provider: str, credentials: dict[str, str]
) -> tuple[dict[str, str], dict[str, str]]:
    """Separa os campos em (segredos, config) conforme o registro do provedor.
    Segredos serão criptografados; config (não sensível) fica em texto puro."""
    definition = get_connector_definition(provider)
    if definition is None:
        raise ValidationError(f"Provedor de integração '{provider}' não é suportado.")
    secrets: dict[str, str] = {}
    config: dict[str, str] = {}
    for field in definition.credential_fields:
        value = credentials.get(field.key, "").strip()
        if not value:
            raise ValidationError(f"O campo '{field.label}' é obrigatório.")
        if field.secret:
            secrets[field.key] = value
        else:
            config[field.key] = value
    return secrets, config


class ConnectProviderUseCase:
    """Conecta a empresa a um provedor: valida credenciais, testa a conexão e
    armazena os segredos criptografados."""

    def __init__(
        self,
        connection_repository: ConnectionRepository,
        cipher: SecretCipher,
        connector: Connector,
    ) -> None:
        self._connection_repository = connection_repository
        self._cipher = cipher
        self._connector = connector

    async def execute(self, *, provider: str, credentials: dict[str, str]) -> Connection:
        secrets, config = split_credentials(provider, credentials)
        # Testa antes de salvar: nunca guardamos credenciais que não funcionam.
        await self._connector.test_connection({**secrets, **config})
        encrypted = self._cipher.encrypt(json.dumps(secrets))
        return await self._connection_repository.upsert(
            provider=provider, encrypted_secrets=encrypted, config=config
        )
