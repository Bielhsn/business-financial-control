from argon2 import PasswordHasher as Argon2Hasher
from argon2.exceptions import Argon2Error, InvalidHashError


class Argon2PasswordHasher:
    """Hash de senhas com Argon2id (vencedor da Password Hashing Competition)."""

    def __init__(self) -> None:
        self._hasher = Argon2Hasher()

    def hash(self, password: str) -> str:
        return self._hasher.hash(password)

    def verify(self, password: str, hashed_password: str) -> bool:
        try:
            return self._hasher.verify(hashed_password, password)
        except (Argon2Error, InvalidHashError):
            # InvalidHashError herda de ValueError, não de Argon2Error, mas também
            # significa apenas "hash armazenado não é um Argon2 válido" — não deve
            # nunca vazar como 500, apenas reportar falha de verificação.
            return False
