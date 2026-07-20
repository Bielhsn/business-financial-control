from typing import Protocol


class CompanyDataExporter(Protocol):
    """Reúne todos os dados de uma empresa num dicionário serializável (LGPD:
    direito de portabilidade). Nunca inclui segredos de integração."""

    async def export(self, company_id: str) -> dict[str, object]: ...


class CompanyDataEraser(Protocol):
    """Apaga a empresa e todos os dados relacionados (LGPD: direito ao
    esquecimento). Operação irreversível."""

    async def erase(self, company_id: str) -> None: ...
