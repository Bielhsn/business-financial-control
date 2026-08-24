"""Sincronização automática.

O risco desta funcionalidade não é falhar — é acertar do jeito errado. Ela roda
fora de requisição, lê conexões de TODAS as empresas e escreve lançamento
financeiro. Se o contexto de empresa escapar, o financeiro de uma vai parar
dentro de outra, e ninguém percebe até a conciliação não fechar.
"""

from datetime import UTC, datetime, timedelta

import pytest

from app.application.connector.scheduled_sync import SyncDueConnectionsUseCase
from app.core.exceptions import ConnectorError
from app.core.tenant import get_current_company_id
from app.domain.connector.entities import Connection

pytestmark = pytest.mark.anyio


def _conexao(company_id: str, provider: str, last_synced_at: datetime | None) -> Connection:
    agora = datetime.now(UTC)
    return Connection(
        id=f"{company_id}-{provider}",
        company_id=company_id,
        provider=provider,
        status="connected",
        config={},
        last_synced_at=last_synced_at,
        last_error=None,
        created_at=agora,
        updated_at=agora,
    )


class FakeDueRepository:
    """Devolve o que foi programado e registra o filtro recebido."""

    def __init__(self, conexoes: list[Connection]) -> None:
        self._conexoes = conexoes
        self.older_than: datetime | None = None
        self.limit: int | None = None

    async def list_due_for_sync(self, *, older_than: datetime, limit: int) -> list[Connection]:
        self.older_than = older_than
        self.limit = limit
        return self._conexoes


async def test_sets_the_company_context_before_syncing_each_one() -> None:
    """O contexto precisa mudar A CADA conexão. Herdar o da anterior escreveria
    o financeiro de uma empresa dentro de outra."""
    vistos: list[tuple[str, str]] = []

    async def sync(company_id: str, provider: str) -> None:
        # Lê do contexto, não do argumento: é assim que os repositórios reais
        # descobrem de quem é o dado.
        vistos.append((get_current_company_id(), provider))

    repo = FakeDueRepository(
        [
            _conexao("empresa-A", "hotmart", None),
            _conexao("empresa-B", "ifood", None),
        ]
    )
    relatorio = await SyncDueConnectionsUseCase(
        repo, sync, stale_after=timedelta(minutes=60)
    ).execute()

    assert vistos == [("empresa-A", "hotmart"), ("empresa-B", "ifood")]
    assert relatorio.succeeded == 2


async def test_one_broken_connection_does_not_stop_the_queue() -> None:
    """Credencial vencida de uma empresa não pode deixar as outras sem
    atualizar — seria uma falha de um virando falha de todos."""
    sincronizadas: list[str] = []

    async def sync(company_id: str, provider: str) -> None:
        if company_id == "empresa-quebrada":
            raise ConnectorError("Credenciais recusadas.")
        sincronizadas.append(company_id)

    repo = FakeDueRepository(
        [
            _conexao("empresa-quebrada", "ifood", None),
            _conexao("empresa-ok", "hotmart", None),
        ]
    )
    relatorio = await SyncDueConnectionsUseCase(
        repo, sync, stale_after=timedelta(minutes=60)
    ).execute()

    assert sincronizadas == ["empresa-ok"]
    assert relatorio.failed == 1
    assert relatorio.succeeded == 1


async def test_unexpected_crash_also_does_not_stop_the_queue() -> None:
    """Erro não previsto é o que mais assusta numa tarefa de fundo: sem captura
    ampla, a fila morre no meio e nada avisa."""

    async def sync(company_id: str, provider: str) -> None:
        raise RuntimeError("algo inesperado")

    repo = FakeDueRepository([_conexao("empresa-A", "ifood", None)])
    relatorio = await SyncDueConnectionsUseCase(
        repo, sync, stale_after=timedelta(minutes=60)
    ).execute()

    assert relatorio.attempted == 1
    assert relatorio.failed == 1


async def test_asks_only_for_connections_older_than_the_interval() -> None:
    async def sync(company_id: str, provider: str) -> None:
        return None

    repo = FakeDueRepository([])
    antes = datetime.now(UTC) - timedelta(minutes=60)
    await SyncDueConnectionsUseCase(repo, sync, stale_after=timedelta(minutes=60)).execute()

    assert repo.older_than is not None
    # Recém-sincronizada não entra: a rodada seguinte tentaria de novo o que
    # acabou de rodar, multiplicando chamada contra o provedor.
    assert abs((repo.older_than - antes).total_seconds()) < 5


async def test_caps_how_many_run_per_round() -> None:
    """Uma base grande não pode virar rajada contra os provedores nem prender o
    processo por minutos a fio."""

    async def sync(company_id: str, provider: str) -> None:
        return None

    repo = FakeDueRepository([])
    await SyncDueConnectionsUseCase(repo, sync, stale_after=timedelta(minutes=60)).execute()

    assert repo.limit is not None and repo.limit <= 50


async def test_nothing_due_is_a_quiet_no_op() -> None:
    chamou = False

    async def sync(company_id: str, provider: str) -> None:
        nonlocal chamou
        chamou = True

    relatorio = await SyncDueConnectionsUseCase(
        FakeDueRepository([]), sync, stale_after=timedelta(minutes=60)
    ).execute()

    assert chamou is False
    assert relatorio.attempted == 0
