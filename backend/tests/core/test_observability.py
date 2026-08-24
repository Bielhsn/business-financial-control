"""Rastreamento de erro — com foco no que NÃO pode sair.

Este sistema guarda dado financeiro de terceiros, credencial de integração e
senha em trânsito. Enviar isso para um serviço externo transformaria uma
ferramenta de diagnóstico num vazamento, e o pior é que funcionaria em silêncio:
o alerta chegaria bonito, com o segredo dentro.
"""

from app.core.config import Settings
from app.core.observability import _before_send, configure_error_tracking


def test_removes_secrets_at_any_depth() -> None:
    """O segredo raramente está na raiz — aparece dentro de headers, de extra,
    de uma lista de breadcrumbs. Filtrar só o primeiro nível daria falsa
    sensação de segurança."""
    evento = {
        "request": {
            "headers": {"Authorization": "Bearer segredo", "User-Agent": "Chrome"},
        },
        "extra": {
            "credentials": {"client_secret": "chave-do-ifood", "client_id": "publico"},
        },
        "breadcrumbs": [{"data": {"password": "senha-do-usuario", "email": "ana@example.com"}}],
    }

    limpo = _before_send(evento, {})

    assert limpo["request"]["headers"]["Authorization"] == "[removido]"
    assert limpo["extra"]["credentials"]["client_secret"] == "[removido]"
    assert limpo["breadcrumbs"][0]["data"]["password"] == "[removido]"


def test_keeps_what_is_useful_for_diagnosis() -> None:
    """Apagar tudo seria seguro e inútil: o alerta precisa dizer o que quebrou."""
    evento = {
        "request": {"url": "/api/v1/companies/1/transactions", "method": "POST"},
        "extra": {"provider": "ifood", "status_code": 500},
    }

    limpo = _before_send(evento, {})

    assert limpo["request"]["url"] == "/api/v1/companies/1/transactions"
    assert limpo["extra"]["provider"] == "ifood"


def test_key_matching_ignores_case() -> None:
    # Cabeçalho HTTP chega em capitalização variada; casar exato deixaria passar.
    limpo = _before_send({"a": {"AUTHORIZATION": "x", "Client_Secret": "y"}}, {})

    assert limpo["a"]["AUTHORIZATION"] == "[removido]"
    assert limpo["a"]["Client_Secret"] == "[removido]"


def test_disabled_without_dsn() -> None:
    """Sem DSN nada é enviado: teste e desenvolvimento não falam com serviço
    externo, e o projeto precisa subir sem conta em lugar nenhum."""
    # Não levanta e não inicializa — a ausência de erro é o comportamento.
    configure_error_tracking(Settings(_env_file=None, sentry_dsn=None))
