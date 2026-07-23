import pytest

from app.api.v1.deps import get_email_sender
from app.core.config import Settings
from app.core.exceptions import AIProviderNotConfiguredError
from app.infrastructure.email.console import ConsoleEmailSender
from app.infrastructure.email.resend import ResendEmailSender


def _settings(**overrides: object) -> Settings:
    return Settings(_env_file=None, **overrides)  # type: ignore[arg-type]


def test_defaults_to_console() -> None:
    assert isinstance(get_email_sender(_settings()), ConsoleEmailSender)


def test_resend_provider_returns_resend_sender() -> None:
    sender = get_email_sender(_settings(email_provider="resend", resend_api_key="re_abc"))
    assert isinstance(sender, ResendEmailSender)


def test_resend_without_key_raises() -> None:
    with pytest.raises(AIProviderNotConfiguredError):
        get_email_sender(_settings(email_provider="resend"))
