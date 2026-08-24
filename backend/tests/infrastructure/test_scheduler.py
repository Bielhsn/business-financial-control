"""O loop de agendamento.

O modo de falha que importa aqui é silencioso e permanente: uma rodada que
estoura encerra a tarefa, o agendamento morre, e só se descobre quando alguém
repara que os números pararam de atualizar.
"""

import asyncio

import pytest

from app.infrastructure.scheduler import PeriodicSyncScheduler

pytestmark = pytest.mark.anyio


async def test_disabled_when_interval_is_zero() -> None:
    """Teste e desenvolvimento não devem sair chamando provedor externo."""
    chamou = False

    async def rodada() -> None:
        nonlocal chamou
        chamou = True

    agendador = PeriodicSyncScheduler(rodada, interval_seconds=0, initial_delay_seconds=0)
    agendador.start()
    await asyncio.sleep(0.05)

    assert chamou is False
    await agendador.stop()


async def test_runs_repeatedly() -> None:
    rodadas = 0

    async def rodada() -> None:
        nonlocal rodadas
        rodadas += 1

    agendador = PeriodicSyncScheduler(rodada, interval_seconds=0.01, initial_delay_seconds=0)
    agendador.start()
    await asyncio.sleep(0.08)
    await agendador.stop()

    assert rodadas >= 2


async def test_a_crashing_round_does_not_kill_the_loop() -> None:
    tentativas = 0

    async def rodada() -> None:
        nonlocal tentativas
        tentativas += 1
        if tentativas == 1:
            raise RuntimeError("primeira rodada quebrou")

    agendador = PeriodicSyncScheduler(rodada, interval_seconds=0.01, initial_delay_seconds=0)
    agendador.start()
    await asyncio.sleep(0.08)
    await agendador.stop()

    # Sobreviveu à primeira falha e continuou tentando.
    assert tentativas >= 2


async def test_stop_is_safe_before_start_and_twice() -> None:
    """O encerramento da aplicação chama `stop` sem saber se `start` rodou;
    estourar aí seguraria o processo no shutdown."""

    async def rodada() -> None:
        return None

    agendador = PeriodicSyncScheduler(rodada, interval_seconds=0.01, initial_delay_seconds=0)
    await agendador.stop()

    agendador.start()
    await agendador.stop()
    await agendador.stop()


async def test_start_twice_does_not_duplicate_the_loop() -> None:
    rodadas = 0

    async def rodada() -> None:
        nonlocal rodadas
        rodadas += 1

    agendador = PeriodicSyncScheduler(rodada, interval_seconds=0.02, initial_delay_seconds=0)
    agendador.start()
    agendador.start()
    await asyncio.sleep(0.05)
    await agendador.stop()

    # Duas tarefas dobrariam a contagem e as chamadas contra o provedor.
    assert rodadas <= 3
