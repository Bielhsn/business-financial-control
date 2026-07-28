"""Envelope de paginação compartilhado pela API.

Listas paginadas devolvem um objeto, não um array puro: sem o `total` a
interface não consegue dizer "1–5 de 312" nem saber quantas páginas existem, e
sem `limit`/`offset` de volta ela não sabe em que página está depois de um
recarregamento. Um único formato para todos os recursos evita que cada tela
aprenda um contrato diferente.
"""

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    # Quantos registros casam com o filtro — não quantos vieram nesta página.
    total: int
    limit: int
    offset: int

    @property
    def has_more(self) -> bool:
        return self.offset + len(self.items) < self.total
