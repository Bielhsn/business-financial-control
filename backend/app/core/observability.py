"""Rastreamento de erro em produção.

Antes disto, uma exceção virava uma linha no log da Render — e log que ninguém
lê não é observabilidade. Os defeitos chegavam por print de cliente no WhatsApp,
o que significa descobrir depois de alguém tropeçar.

**Opcional de propósito.** Sem `SENTRY_DSN` nada é enviado: desenvolvimento e
testes não devem falar com serviço externo, e um projeto clonado precisa subir
sem depender de conta em lugar nenhum.

**O que NÃO sai daqui importa mais que o que sai.** Este sistema guarda dado
financeiro de terceiros, credencial de integração e senha em trânsito. Enviar
corpo de requisição para um serviço externo transformaria uma ferramenta de
diagnóstico num vazamento — então PII fica desligado e há um filtro explícito
sobre o que escapa.
"""

from typing import Any

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration
from sentry_sdk.types import Event, Hint

from app.core.config import Settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Cabeçalhos e campos que nunca podem sair da aplicação, mesmo por engano.
_SENSITIVE_KEYS = frozenset(
    {
        "authorization",
        "cookie",
        "set-cookie",
        "x-api-key",
        "password",
        "password_confirmation",
        "hashed_password",
        "client_secret",
        "access_token",
        "refresh_token",
        "api_key",
        "secret",
        "token",
    }
)

_REDACTED = "[removido]"


def _scrub(value: Any) -> Any:
    """Percorre a estrutura e apaga o que for sensível, em qualquer profundidade.

    A varredura recursiva existe porque o segredo raramente está na raiz: ele
    aparece dentro de `request.headers`, de `extra.credentials`, de uma lista de
    breadcrumbs. Filtrar só o primeiro nível daria falsa sensação de segurança.
    """
    if isinstance(value, dict):
        return {
            chave: (_REDACTED if str(chave).lower() in _SENSITIVE_KEYS else _scrub(item))
            for chave, item in value.items()
        }
    if isinstance(value, list):
        return [_scrub(item) for item in value]
    return value


def _before_send(event: Event, _hint: Hint) -> Event | None:
    return _scrub(event)  # type: ignore[no-any-return]


def configure_error_tracking(settings: Settings) -> None:
    if not settings.sentry_dsn:
        logger.info("error_tracking_disabled", reason="SENTRY_DSN ausente")
        return

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        # Amostragem de performance fica em zero: o objetivo aqui é saber que
        # quebrou, não medir latência. Traces custam cota e ruído.
        traces_sample_rate=0.0,
        # Nunca enviar dados pessoais por padrão — vale mais o diagnóstico
        # incompleto que o vazamento completo.
        send_default_pii=False,
        max_request_body_size="never",
        before_send=_before_send,
        integrations=[
            StarletteIntegration(failed_request_status_codes={500, 502, 503, 504}),
            FastApiIntegration(failed_request_status_codes={500, 502, 503, 504}),
        ],
    )
    logger.info("error_tracking_enabled", environment=settings.environment)


def report_exception(exc: Exception, **context: object) -> None:
    """Envia uma exceção já tratada, com contexto.

    Chamado do handler de exceção não tratada: sem isto, o 500 devolvido ao
    cliente sumiria do radar assim que a resposta fosse escrita.
    """
    if not sentry_sdk.is_initialized():
        return
    with sentry_sdk.new_scope() as scope:
        for chave, valor in context.items():
            scope.set_tag(chave, str(valor))
        sentry_sdk.capture_exception(exc)
