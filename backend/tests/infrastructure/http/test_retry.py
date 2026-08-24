"""Transporte que repete falhas temporárias.

O que **não** é repetido importa tanto quanto o que é: repetir credencial
inválida só multiplica chamada contra o provedor e atrasa o erro que o lojista
precisa ver.
"""

import httpx
import pytest

from app.infrastructure.http.retry import RetryTransport, backoff_delay

pytestmark = pytest.mark.anyio


class _SleepSpy:
    """Substitui o sleep real: o teste mede a espera sem gastá-la."""

    def __init__(self) -> None:
        self.delays: list[float] = []

    async def __call__(self, delay: float) -> None:
        self.delays.append(delay)


def _sequence(responses: list[object]) -> tuple[httpx.MockTransport, list[int]]:
    """Transporte que devolve as respostas em ordem; itens Exception são levantados."""
    calls = [0]

    def handler(request: httpx.Request) -> httpx.Response:
        item = responses[min(calls[0], len(responses) - 1)]
        calls[0] += 1
        if isinstance(item, Exception):
            raise item
        assert isinstance(item, httpx.Response)
        return item

    return httpx.MockTransport(handler), calls


async def _get(transport: RetryTransport) -> httpx.Response:
    async with httpx.AsyncClient(transport=transport) as client:
        return await client.get("https://provedor.test/vendas")


async def test_server_error_is_retried_until_it_succeeds() -> None:
    inner, calls = _sequence(
        [httpx.Response(503), httpx.Response(503), httpx.Response(200, json={"ok": True})]
    )
    sleep = _SleepSpy()

    response = await _get(RetryTransport(inner, sleep=sleep))

    assert response.status_code == 200
    assert calls[0] == 3
    assert len(sleep.delays) == 2  # esperou entre as tentativas


async def test_timeout_is_retried() -> None:
    inner, calls = _sequence(
        [httpx.TimeoutException("demorou"), httpx.Response(200, json={"ok": True})]
    )

    response = await _get(RetryTransport(inner, sleep=_SleepSpy()))

    assert response.status_code == 200
    assert calls[0] == 2


async def test_permission_error_is_not_retried() -> None:
    """403 não melhora na segunda tentativa — é o erro que o lojista precisa ver."""
    inner, calls = _sequence([httpx.Response(403, json={"message": "forbidden"})])
    sleep = _SleepSpy()

    response = await _get(RetryTransport(inner, sleep=sleep))

    assert response.status_code == 403
    assert calls[0] == 1
    assert sleep.delays == []


async def test_invalid_credentials_are_not_retried() -> None:
    inner, calls = _sequence([httpx.Response(401)])

    response = await _get(RetryTransport(inner, sleep=_SleepSpy()))

    assert response.status_code == 401
    assert calls[0] == 1


async def test_rate_limit_obeys_retry_after() -> None:
    """O servidor sabe melhor que nós quando volta a aceitar."""
    inner, _ = _sequence(
        [httpx.Response(429, headers={"Retry-After": "7"}), httpx.Response(200, json={})]
    )
    sleep = _SleepSpy()

    response = await _get(RetryTransport(inner, sleep=sleep))

    assert response.status_code == 200
    assert sleep.delays == [7.0]


async def test_gives_up_and_returns_the_last_response() -> None:
    """Depois do limite, o erro do provedor chega a quem chamou — não vira
    silêncio nem exceção genérica."""
    inner, calls = _sequence([httpx.Response(503)])

    response = await _get(RetryTransport(inner, attempts=3, sleep=_SleepSpy()))

    assert response.status_code == 503
    assert calls[0] == 3


async def test_network_error_after_all_attempts_is_raised() -> None:
    inner, _ = _sequence([httpx.ConnectError("sem rota")])

    with pytest.raises(httpx.ConnectError):
        await _get(RetryTransport(inner, attempts=2, sleep=_SleepSpy()))


def test_backoff_grows_and_stays_bounded() -> None:
    # jitter fixo em 1.0 remove a aleatoriedade e deixa a progressão visível.
    delays = [backoff_delay(n, jitter=1.0) for n in range(1, 7)]

    assert delays == sorted(delays)  # cresce
    assert delays[0] < delays[-1]
    assert max(delays) <= 8.0  # com teto


def test_backoff_jitter_spreads_retries() -> None:
    """Sem jitter, várias sincronizações que falharam juntas voltariam no mesmo
    instante e derrubariam o provedor de novo."""
    assert backoff_delay(3, jitter=0.0) < backoff_delay(3, jitter=1.0)
