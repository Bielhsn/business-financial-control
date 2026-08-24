"""Loop que dispara a sincronização periódica.

Roda dentro do próprio processo da API, como tarefa asyncio. É a opção mais
simples que resolve o problema hoje, e as alternativas custavam mais do que
entregavam nesta escala: um worker separado dobra o serviço na Render, e um cron
externo exige endpoint autenticado só para ser chamado de fora.

**Duas ressalvas honestas sobre essa escolha:**

1. Com mais de uma instância da API, todas rodam o loop e a mesma conexão é
   sincronizada em paralelo. Isso não corrompe dado — a importação é idempotente
   por `external_ref`, com índice único no banco —, mas desperdiça chamada
   contra o provedor. Quando houver escala horizontal, isto vira cron externo ou
   ganha trava distribuída.
2. Em planos que hibernam por inatividade, o processo dorme e o loop para junto.
   O agendamento só é confiável em serviço que fica de pé.

Desligado por padrão (`SYNC_INTERVAL_MINUTES=0`): teste e desenvolvimento não
devem sair chamando provedor externo sozinhos.
"""

import asyncio
import contextlib
from collections.abc import Awaitable, Callable

from app.core.logging import get_logger

logger = get_logger(__name__)


class PeriodicSyncScheduler:
    def __init__(
        self,
        run_once: Callable[[], Awaitable[object]],
        *,
        interval_seconds: float,
        initial_delay_seconds: float = 30.0,
    ) -> None:
        self._run_once = run_once
        self._interval = interval_seconds
        # Espera antes da primeira rodada: subir a aplicação e já disparar
        # sincronização competiria com o tráfego de quem está reconectando
        # logo após um deploy.
        self._initial_delay = initial_delay_seconds
        self._task: asyncio.Task[None] | None = None

    async def _loop(self) -> None:
        await asyncio.sleep(self._initial_delay)
        while True:
            try:
                await self._run_once()
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001 - o loop não pode morrer
                # Uma rodada que explode não pode encerrar o agendamento: seria
                # uma falha silenciosa e permanente, do tipo que só se descobre
                # quando alguém repara que os números pararam de atualizar.
                logger.error("scheduled_sync_round_crashed", error=str(exc))
            await asyncio.sleep(self._interval)

    def start(self) -> None:
        if self._interval <= 0:
            logger.info("scheduled_sync_disabled", reason="SYNC_INTERVAL_MINUTES=0")
            return
        if self._task is not None:
            return
        self._task = asyncio.create_task(self._loop())
        logger.info("scheduled_sync_scheduled", interval_seconds=self._interval)

    async def stop(self) -> None:
        if self._task is None:
            return
        self._task.cancel()
        # A tarefa sempre levanta CancelledError ao ser cancelada; esperar por
        # ela é o que garante que o loop terminou antes do processo seguir.
        with contextlib.suppress(asyncio.CancelledError):
            await self._task
        self._task = None
        logger.info("scheduled_sync_stopped")
