from datetime import UTC, datetime, timedelta
from urllib.parse import quote

from app.core.config import Settings
from app.core.exceptions import ValidationError
from app.domain.auth.ports import PasswordHasher
from app.domain.auth.repository import RefreshTokenRepository
from app.domain.auth.verification import (
    VerificationCodeRepository,
    VerificationPurpose,
    generate_token,
    hash_code,
)
from app.domain.notifications.email import EmailMessage, EmailSender
from app.domain.user.repository import UserRepository


def _reset_link(app_base_url: str, *, email: str, token: str) -> str:
    return f"{app_base_url.rstrip('/')}/redefinir-senha?email={quote(email)}&token={quote(token)}"


class RequestPasswordResetUseCase:
    """Envia um código de redefinição. Nunca revela se o e-mail existe (resposta
    idêntica em ambos os casos) — evita enumeração de contas."""

    def __init__(
        self,
        user_repository: UserRepository,
        code_repository: VerificationCodeRepository,
        email_sender: EmailSender,
        settings: Settings,
    ) -> None:
        self._user_repository = user_repository
        self._code_repository = code_repository
        self._email_sender = email_sender
        self._settings = settings

    async def execute(self, *, email: str) -> None:
        user = await self._user_repository.get_by_email(email.strip().lower())
        if user is None:
            return  # silencioso de propósito

        token = generate_token()
        token_hash = hash_code(
            token,
            secret=self._settings.secret_key,
            user_id=user.id,
            purpose=VerificationPurpose.PASSWORD_RESET,
        )
        await self._code_repository.invalidate_for(
            user_id=user.id, purpose=VerificationPurpose.PASSWORD_RESET
        )
        await self._code_repository.create(
            user_id=user.id,
            purpose=VerificationPurpose.PASSWORD_RESET,
            code_hash=token_hash,
            expires_at=datetime.now(UTC)
            + timedelta(minutes=self._settings.password_reset_ttl_minutes),
        )
        link = _reset_link(self._settings.app_base_url, email=user.email, token=token)
        await self._email_sender.send(
            EmailMessage(
                to=user.email,
                subject="Redefinição de senha — Aurum OS",
                body=(
                    "Recebemos um pedido para redefinir sua senha no Aurum OS. "
                    f"Clique no link abaixo para escolher uma nova senha:\n\n{link}\n\n"
                    f"O link expira em {self._settings.password_reset_ttl_minutes} minutos. "
                    "Se você não pediu isso, ignore este e-mail."
                ),
            )
        )


class ResetPasswordUseCase:
    def __init__(
        self,
        user_repository: UserRepository,
        code_repository: VerificationCodeRepository,
        refresh_token_repository: RefreshTokenRepository,
        password_hasher: PasswordHasher,
        settings: Settings,
    ) -> None:
        self._user_repository = user_repository
        self._code_repository = code_repository
        self._refresh_token_repository = refresh_token_repository
        self._password_hasher = password_hasher
        self._settings = settings

    async def execute(self, *, email: str, code: str, new_password: str) -> None:
        user = await self._user_repository.get_by_email(email.strip().lower())
        if user is None:
            raise ValidationError("Código inválido ou expirado.")

        code_hash = hash_code(
            code.strip(),
            secret=self._settings.secret_key,
            user_id=user.id,
            purpose=VerificationPurpose.PASSWORD_RESET,
        )
        active = await self._code_repository.get_active(
            user_id=user.id, purpose=VerificationPurpose.PASSWORD_RESET, code_hash=code_hash
        )
        if active is None:
            raise ValidationError("Código inválido ou expirado.")

        await self._code_repository.mark_used(active.id)
        await self._user_repository.update(
            user.id, hashed_password=self._password_hasher.hash(new_password), is_verified=True
        )
        # Redefinir senha invalida todas as sessões antigas (segurança).
        await self._refresh_token_repository.revoke_all_for_user(user.id)
