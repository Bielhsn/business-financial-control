"""Transporte HTTP que repete falhas temporárias.

Fica na camada de transporte de propósito. As alternativas eram piores:

- dentro de cada conector: a mesma lógica duplicada em Hotmart, iFood e em todo
  provedor futuro;
- em volta de `fetch_sales`: granularidade errada — uma falha na página 40
  refaria as 39 anteriores.

Aqui a repetição é da requisição que falhou, vale para qualquer conector sem
que ele saiba que existe, e os testes seguem determinísticos porque continuam
injetando o próprio transporte.

O que **não** é repetido importa tanto quanto o que é: 401, 403 e 404 não
melhoram na segunda tentativa. Repetir credencial inválida só multiplica
chamada contra o provedor e atrasa o erro que o lojista precisa ver.
"""

import asyncio
import random

import httpx

from app.core.logging import get_logger

logger = get_logger(__name__)

# Erros de servidor e de infraestrutura de borda — tipicamente passageiros.
_RETRIABLE_STATUS = frozenset({429, 500, 502, 503, 504})
_DEFAULT_ATTEMPTS = 3
_BASE_DELAY_SECONDS = 0.5
_MAX_DELAY_SECONDS = 8.0


def _retry_after_seconds(response: httpx.Response) -> float | None:
    """Lê o `Retry-After` da resposta. O servidor sabe melhor que nós quando
    volta a aceitar — quando ele diz, obedecemos em vez de usar o backoff."""
    raw = response.headers.get("retry-after")
    if not raw:
        return None
    try:
        # Só a forma em segundos; a forma com data HTTP é rara nestas APIs.
        return max(0.0, float(raw.strip()))
    except ValueError:
        return None


def backoff_delay(attempt: int, *, jitter: float | None = None) -> float:
    """Espera exponencial com jitter, em segundos, para a tentativa `attempt`
    (base 1).

    O jitter evita o "efeito manada": sem ele, várias sincronizações que
    falharam juntas voltariam exatamente no mesmo instante e derrubariam o
    provedor de novo.
    """
    ceiling: float = min(_BASE_DELAY_SECONDS * (2 ** (attempt - 1)), _MAX_DELAY_SECONDS)
    factor: float = random.random() if jitter is None else jitter
    return ceiling * (0.5 + 0.5 * factor)


class RetryTransport(httpx.AsyncBaseTransport):
    """Embrulha um transporte real e repete o que é temporário."""

    def __init__(
        self,
        wrapped: httpx.AsyncBaseTransport | None = None,
        *,
        attempts: int = _DEFAULT_ATTEMPTS,
        sleep: object = None,
    ) -> None:
        self._wrapped = wrapped or httpx.AsyncHTTPTransport()
        self._attempts = max(1, attempts)
        # Injetável para o teste não gastar tempo de parede dormindo de verdade.
        self._sleep = sleep or asyncio.sleep

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        last_error: Exception | None = None

        for attempt in range(1, self._attempts + 1):
            try:
                response = await self._wrapped.handle_async_request(request)
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                last_error = exc
                if attempt == self._attempts:
                    break
                await self._wait(backoff_delay(attempt), request, attempt, str(exc))
                continue

            if response.status_code not in _RETRIABLE_STATUS or attempt == self._attempts:
                return response

            # Precisa ser lido antes de descartar: a resposta será substituída
            # pela da próxima tentativa.
            await response.aread()
            delay = _retry_after_seconds(response) or backoff_delay(attempt)
            await response.aclose()
            await self._wait(delay, request, attempt, f"HTTP {response.status_code}")

        assert last_error is not None
        raise last_error

    async def _wait(self, delay: float, request: httpx.Request, attempt: int, reason: str) -> None:
        logger.info(
            "http_retry_scheduled",
            host=request.url.host,
            path=request.url.path,
            attempt=attempt,
            delay_seconds=round(delay, 3),
            reason=reason,
        )
        await self._sleep(delay)  # type: ignore[operator]

    async def aclose(self) -> None:
        await self._wrapped.aclose()
