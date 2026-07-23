"""Adaptador de e-mail via Resend (https://resend.com).

Envia de verdade, chamando a API HTTP do Resend. O cliente HTTP é injetável
(`httpx.MockTransport`) para os testes rodarem sem tocar a rede. Ativado em
produção por `EMAIL_PROVIDER=resend` + `RESEND_API_KEY` (veja get_email_sender)."""

import httpx

from app.core.exceptions import ExternalServiceError
from app.core.logging import get_logger
from app.domain.notifications.email import EmailMessage

logger = get_logger(__name__)

_DEFAULT_BASE_URL = "https://api.resend.com"
_TIMEOUT = httpx.Timeout(15.0)


class ResendEmailSender:
    """Implementa EmailSender enviando pela API do Resend."""

    def __init__(
        self,
        *,
        api_key: str,
        sender: str,
        base_url: str = _DEFAULT_BASE_URL,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._api_key = api_key
        self._sender = sender
        self._base_url = base_url.rstrip("/")
        self._transport = transport

    async def send(self, message: EmailMessage) -> None:
        payload = {
            "from": self._sender,
            "to": [message.to],
            "subject": message.subject,
            "text": message.body,
        }
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT, transport=self._transport) as client:
                response = await client.post(
                    f"{self._base_url}/emails",
                    json=payload,
                    headers={"Authorization": f"Bearer {self._api_key}"},
                )
        except httpx.HTTPError as exc:
            raise ExternalServiceError("Não foi possível enviar o e-mail (Resend).") from exc

        if response.status_code >= 400:
            logger.warning("resend_email_failed", status=response.status_code, to=message.to)
            raise ExternalServiceError(
                f"O provedor de e-mail recusou o envio (HTTP {response.status_code})."
            )
        logger.info("email_sent_resend", to=message.to, subject=message.subject)
