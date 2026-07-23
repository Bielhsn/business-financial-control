import httpx
import pytest

from app.core.exceptions import ExternalServiceError
from app.domain.notifications.email import EmailMessage
from app.infrastructure.email.resend import ResendEmailSender

pytestmark = pytest.mark.anyio

_BASE = "https://resend.test"


def _sender(handler: object) -> ResendEmailSender:
    transport = httpx.MockTransport(handler)  # type: ignore[arg-type]
    return ResendEmailSender(
        api_key="re_test_key",
        sender="Aurum OS <no-reply@aurum.app>",
        base_url=_BASE,
        transport=transport,
    )


async def test_send_posts_to_resend_with_auth_and_payload() -> None:
    seen: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["auth"] = request.headers.get("Authorization")
        seen["json"] = request.read().decode()
        return httpx.Response(200, json={"id": "email-123"})

    await _sender(handler).send(
        EmailMessage(to="cliente@example.com", subject="Seu código", body="123456")
    )

    assert seen["url"] == f"{_BASE}/emails"
    assert seen["auth"] == "Bearer re_test_key"
    assert "cliente@example.com" in seen["json"]  # type: ignore[operator]
    assert "123456" in seen["json"]  # type: ignore[operator]


async def test_send_raises_on_error_status() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(422, json={"message": "invalid from"})

    with pytest.raises(ExternalServiceError):
        await _sender(handler).send(EmailMessage(to="x@example.com", subject="s", body="b"))


async def test_send_raises_on_network_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom")

    with pytest.raises(ExternalServiceError):
        await _sender(handler).send(EmailMessage(to="x@example.com", subject="s", body="b"))
