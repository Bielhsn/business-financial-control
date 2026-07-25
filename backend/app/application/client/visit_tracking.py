"""Regra compartilhada: uma receita paga vinculada a um cliente conta como
atendimento. Usada tanto ao criar o lançamento já pago quanto ao marcar um
lançamento pendente como pago — nos dois casos o dono não precisa marcar a
visita à mão."""

from datetime import UTC, datetime

from app.domain.client.repository import ClientRepository


def as_utc(moment: datetime) -> datetime:
    """Datas sem fuso vindas da API são tratadas como UTC, para poder comparar
    com o last_visit_at gravado (sempre timezone-aware)."""
    return moment if moment.tzinfo is not None else moment.replace(tzinfo=UTC)


def is_newer_visit(last_visit_at: datetime | None, candidate: datetime) -> bool:
    """Só avança no tempo: um lançamento retroativo não "desatualiza" a data."""
    return last_visit_at is None or as_utc(candidate) > as_utc(last_visit_at)


async def record_visit_if_newer(
    client_repository: ClientRepository, *, client_id: str, visited_at: datetime
) -> None:
    client = await client_repository.get_by_id(client_id)
    if client is None:
        return
    if is_newer_visit(client.last_visit_at, visited_at):
        await client_repository.update(client_id, last_visit_at=as_utc(visited_at))
