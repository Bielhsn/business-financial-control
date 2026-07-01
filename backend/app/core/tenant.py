from contextvars import ContextVar
from dataclasses import dataclass

from app.domain.company.roles import CompanyRole

_current_company_id: ContextVar[str | None] = ContextVar("current_company_id", default=None)


@dataclass
class CompanyContext:
    company_id: str
    role: CompanyRole


def set_current_company_id(company_id: str) -> None:
    _current_company_id.set(company_id)


def get_current_company_id() -> str:
    """Usado pelos repositórios com dados por empresa para filtrar toda leitura/escrita.

    Levanta RuntimeError (erro de programação, não erro de negócio) se nenhuma
    dependência de contexto de empresa foi resolvida antes — nunca retorna dados
    de todas as empresas por omissão.
    """
    company_id = _current_company_id.get()
    if company_id is None:
        raise RuntimeError("Nenhum contexto de empresa (tenant) foi definido para esta requisição.")
    return company_id
