from datetime import UTC, datetime, timedelta

from app.core.config import Settings
from app.core.exceptions import NotFoundError, ValidationError
from app.domain.auth.verification import (
    VerificationCodeRepository,
    VerificationPurpose,
    generate_code,
    hash_code,
)
from app.domain.notifications.email import EmailMessage, EmailSender
from app.domain.user.repository import UserRepository


class RequestEmailVerificationUseCase:
    """Gera um código de 6 dígitos e o envia por e-mail (invalidando anteriores)."""

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

    async def execute(self, *, user_id: str) -> None:
        user = await self._user_repository.get_by_id(user_id)
        if user is None:
            raise NotFoundError("Usuário não encontrado.")
        if user.is_verified:
            return

        code = generate_code()
        code_hash = hash_code(
            code,
            secret=self._settings.secret_key,
            user_id=user.id,
            purpose=VerificationPurpose.EMAIL_VERIFY,
        )
        await self._code_repository.invalidate_for(
            user_id=user.id, purpose=VerificationPurpose.EMAIL_VERIFY
        )
        await self._code_repository.create(
            user_id=user.id,
            purpose=VerificationPurpose.EMAIL_VERIFY,
            code_hash=code_hash,
            expires_at=datetime.now(UTC)
            + timedelta(minutes=self._settings.verification_code_ttl_minutes),
        )
        await self._email_sender.send(
            EmailMessage(
                to=user.email,
                subject="Seu código de confirmação — Aurum OS",
                body=f"Olá! Seu código de confirmação é {code}. "
                f"Ele expira em {self._settings.verification_code_ttl_minutes} minutos.",
            )
        )


class VerifyEmailUseCase:
    def __init__(
        self,
        user_repository: UserRepository,
        code_repository: VerificationCodeRepository,
        settings: Settings,
    ) -> None:
        self._user_repository = user_repository
        self._code_repository = code_repository
        self._settings = settings

    async def execute(self, *, user_id: str, code: str) -> None:
        code_hash = hash_code(
            code.strip(),
            secret=self._settings.secret_key,
            user_id=user_id,
            purpose=VerificationPurpose.EMAIL_VERIFY,
        )
        active = await self._code_repository.get_active(
            user_id=user_id, purpose=VerificationPurpose.EMAIL_VERIFY, code_hash=code_hash
        )
        if active is None:
            raise ValidationError("Código inválido ou expirado.")
        await self._code_repository.mark_used(active.id)
        await self._user_repository.update(user_id, is_verified=True)
