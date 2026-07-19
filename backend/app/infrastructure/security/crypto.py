import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import Settings


def _derive_fernet_key(secret: str) -> bytes:
    """Deriva uma chave Fernet válida (32 bytes base64 urlsafe) de um segredo
    arbitrário, para o operador não precisar gerar o formato exato à mão."""
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


class FernetSecretCipher:
    """Criptografia simétrica autenticada (Fernet/AES-128-CBC + HMAC) para os
    segredos de integração em repouso. A chave vem de `connector_secret_key`
    (ou, na sua ausência, é derivada de `secret_key`)."""

    def __init__(self, settings: Settings) -> None:
        source = settings.connector_secret_key or settings.secret_key
        self._fernet = Fernet(_derive_fernet_key(source))

    def encrypt(self, plaintext: str) -> str:
        return self._fernet.encrypt(plaintext.encode("utf-8")).decode("utf-8")

    def decrypt(self, token: str) -> str:
        try:
            return self._fernet.decrypt(token.encode("utf-8")).decode("utf-8")
        except InvalidToken as exc:  # pragma: no cover - só ocorre se a chave mudar
            raise ValueError("Não foi possível descriptografar o segredo da integração.") from exc
