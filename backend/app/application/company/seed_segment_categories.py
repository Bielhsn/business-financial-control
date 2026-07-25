"""Semeadura das categorias financeiras a partir do perfil do segmento.

Antes, uma empresa nova nascia com o financeiro vazio e o dono precisava inventar
as categorias do zero (ou gerar o blueprint por IA, que exige chave configurada).
Agora a barbearia já começa com "Serviços", "Comissões" e "Produtos e insumos";
a loja de bebidas, com "Compra de mercadorias" e "Taxas de aplicativos".

Determinístico e idempotente: categorias com nome repetido são ignoradas, então
rodar de novo não duplica nada.
"""

from app.core.exceptions import ConflictError
from app.core.tenant import set_current_company_id
from app.domain.company.entities import Company
from app.domain.financial.entities import FinancialCategoryType
from app.domain.financial.repository import FinancialCategoryRepository
from app.domain.segment.registry import resolve_segment_profile


class SeedSegmentCategoriesUseCase:
    def __init__(self, category_repository: FinancialCategoryRepository) -> None:
        self._category_repository = category_repository

    async def execute(self, *, company: Company) -> int:
        """Cria as categorias do segmento e devolve quantas foram criadas."""
        profile = resolve_segment_profile(company.segment, company.subsegment)

        # Os repositórios com dados por empresa leem o tenant do contexto; na
        # criação da empresa ainda não há requisição "dentro" dela.
        set_current_company_id(company.id)

        created = 0
        planned = [(name, FinancialCategoryType.INCOME) for name in profile.income_categories] + [
            (name, FinancialCategoryType.EXPENSE) for name in profile.expense_categories
        ]

        for name, category_type in planned:
            try:
                await self._category_repository.create(name=name, type=category_type)
                created += 1
            except ConflictError:
                # Já existe (empresa recriada ou semeadura repetida) — segue.
                continue
        return created
