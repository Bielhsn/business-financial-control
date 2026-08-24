"""Sincronização automática das conexões.

Até aqui, as vendas do iFood ou da Hotmart só entravam quando alguém clicava em
"Sincronizar". Um painel financeiro que atualiza quando o dono lembra de clicar
não é automático — é importação manual com botão bonito. E como o dono esquece,
ele abre o painel, vê número velho e para de confiar. Perder a confiança no
número é o defeito mais caro num produto financeiro.

**O ponto delicado é o isolamento entre empresas.** O agendador roda fora de
requisição: não há usuário nem empresa no contexto. Ele lê conexões de todos os
inquilinos e, para cada uma, define o contexto ANTES de tocar em qualquer dado.
Errar aqui misturaria o financeiro de uma empresa com o de outra — por isso o
`set_current_company_id` vem antes de construir o caso de uso, e não depois.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.core.exceptions import AppError
from app.core.logging import get_logger
from app.core.tenant import set_current_company_id
from app.domain.connector.repository import ConnectionRepository

logger = get_logger(__name__)

# Teto por rodada: uma base grande não pode virar uma rajada contra os
# provedores nem prender o processo por minutos a fio.
_MAX_POR_RODADA = 20

# Autor dos lançamentos criados sem ninguém logado. Identificável no histórico:
# o dono precisa distinguir o que ele lançou do que a integração trouxe.
SCHEDULER_ACTOR = "scheduler"


@dataclass
class ScheduledSyncReport:
    attempted: int = 0
    succeeded: int = 0
    failed: int = 0


class SyncDueConnectionsUseCase:
    """Sincroniza as conexões vencidas, uma empresa de cada vez."""

    def __init__(
        self,
        connection_repository: ConnectionRepository,
        sync_for_company: Callable[[str, str], object],
        *,
        stale_after: timedelta,
    ) -> None:
        self._connections = connection_repository
        # Recebe (company_id, provider) e devolve um awaitable. Injetado para o
        # agendador não precisar conhecer repositórios, cifra nem conectores.
        self._sync_for_company = sync_for_company
        self._stale_after = stale_after

    async def execute(self) -> ScheduledSyncReport:
        limite = datetime.now(UTC) - self._stale_after
        vencidas = await self._connections.list_due_for_sync(
            older_than=limite, limit=_MAX_POR_RODADA
        )
        report = ScheduledSyncReport()
        if not vencidas:
            return report

        logger.info("scheduled_sync_started", due=len(vencidas))
        for conexao in vencidas:
            report.attempted += 1
            # ANTES de qualquer leitura ou escrita: sem isto o caso de uso
            # herdaria o contexto da conexão anterior e escreveria o
            # financeiro de uma empresa dentro de outra.
            set_current_company_id(conexao.company_id)
            try:
                await self._sync_for_company(conexao.company_id, conexao.provider)  # type: ignore[misc]
                report.succeeded += 1
            except AppError as exc:
                # Uma empresa com credencial vencida não pode parar a fila das
                # outras. O erro já foi persistido na conexão pelo sync.
                report.failed += 1
                logger.warning(
                    "scheduled_sync_connection_failed",
                    company_id=conexao.company_id,
                    provider=conexao.provider,
                    reason=exc.message,
                )
            except Exception as exc:  # noqa: BLE001 - a fila precisa sobreviver
                report.failed += 1
                logger.error(
                    "scheduled_sync_connection_crashed",
                    company_id=conexao.company_id,
                    provider=conexao.provider,
                    error=str(exc),
                )

        logger.info(
            "scheduled_sync_finished",
            attempted=report.attempted,
            succeeded=report.succeeded,
            failed=report.failed,
        )
        return report
