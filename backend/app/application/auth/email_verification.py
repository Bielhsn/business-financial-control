from datetime import UTC, datetime, timedelta
from urllib.parse import quote

from app.core.config import Settings
from app.core.exceptions import NotFoundError, ValidationError
from app.domain.auth.verification import (
    VerificationCodeRepository,
    VerificationPurpose,
    generate_token,
    hash_code,
)
from app.domain.notifications.email import EmailMessage, EmailSender
from app.domain.user.entities import User
from app.domain.user.repository import UserRepository


def _verify_link(app_base_url: str, *, email: str, token: str) -> str:
    return f"{app_base_url.rstrip('/')}/verificar-email?email={quote(email)}&token={quote(token)}"


class RequestEmailVerificationUseCase:
    """Envia um LINK de confirmação por e-mail (invalidando os anteriores). A conta
    fica bloqueada no login até a pessoa clicar no link."""

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
        await self._send(user)

    async def execute_by_email(self, *, email: str) -> None:
        # Usado no fluxo público de "reenviar confirmação" (a pessoa ainda não
        # logou). Silencioso quando o e-mail não existe — não vaza cadastro.
        user = await self._user_repository.get_by_email(email.strip().lower())
        if user is not None:
            await self._send(user)

    async def _send(self, user: User) -> None:
        if user.is_verified:
            return
        token = generate_token()
        token_hash = hash_code(
            token,
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
            code_hash=token_hash,
            expires_at=datetime.now(UTC)
            + timedelta(minutes=self._settings.verification_code_ttl_minutes),
        )
        link = _verify_link(self._settings.app_base_url, email=user.email, token=token)
        await self._email_sender.send(
            EmailMessage(
                to=user.email,
                subject="Confirme seu e-mail — Aurum OS",
                body=(
                    "Olá! Confirme seu e-mail para ativar sua conta no Aurum OS clicando "
                    f"no link abaixo:\n\n{link}\n\n"
                    f"O link expira em {self._settings.verification_code_ttl_minutes} minutos. "
                    "Se você não criou esta conta, ignore este e-mail."
                ),
            )
        )


class ConfirmEmailByTokenUseCase:
    """Confirma o e-mail a partir do token do link (fluxo público, sem login)."""

    def __init__(
        self,
        user_repository: UserRepository,
        code_repository: VerificationCodeRepository,
        settings: Settings,
    ) -> None:
        self._user_repository = user_repository
        self._code_repository = code_repository
        self._settings = settings

    async def execute(self, *, email: str, token: str) -> None:
        user = await self._user_repository.get_by_email(email.strip().lower())
        if user is None:
            raise ValidationError("Link inválido ou expirado.")
        if user.is_verified:
            return  # idempotente: clicar de novo não dá erro
        token_hash = hash_code(
            token.strip(),
            secret=self._settings.secret_key,
            user_id=user.id,
            purpose=VerificationPurpose.EMAIL_VERIFY,
        )
        active = await self._code_repository.get_active(
            user_id=user.id, purpose=VerificationPurpose.EMAIL_VERIFY, code_hash=token_hash
        )
        if active is None:
            raise ValidationError("Link inválido ou expirado.")
        await self._code_repository.mark_used(active.id)
        await self._user_repository.update(user.id, is_verified=True)


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
