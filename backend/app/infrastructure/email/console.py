from app.core.logging import get_logger
from app.domain.notifications.email import EmailMessage

logger = get_logger(__name__)


class ConsoleEmailSender:
    """Adaptador de e-mail para desenvolvimento: registra a mensagem no log em vez
    de enviar de verdade. Em produção, troque por um adaptador SMTP/provedor real
    (a porta EmailSender permite plugar sem mudar os use cases)."""

    async def send(self, message: EmailMessage) -> None:
        logger.info(
            "email_sent_console",
            to=message.to,
            subject=message.subject,
            body=message.body,
        )
