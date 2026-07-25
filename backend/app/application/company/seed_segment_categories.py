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
from app.domain.financial.entities import FinancialCategory, FinancialCategoryType
from app.domain.financial.repository import FinancialCategoryRepository
from app.domain.segment.registry import resolve_segment_profile


class SeedSegmentCategoriesUseCase:
    def __init__(self, category_repository: FinancialCategoryRepository) -> None:
        self._category_repository = category_repository

    async def execute(self, *, company: Company) -> list[FinancialCategory]:
        """Cria as categorias do segmento e devolve as que foram criadas agora
        (as que já existiam ficam de fora, sem erro)."""
        profile = resolve_segment_profile(company.segment, company.subsegment)

        # Os repositórios com dados por empresa leem o tenant do contexto; na
        # criação da empresa ainda não há requisição "dentro" dela.
        set_current_company_id(company.id)

        created: list[FinancialCategory] = []
        planned = [(name, FinancialCategoryType.INCOME) for name in profile.income_categories] + [
            (name, FinancialCategoryType.EXPENSE) for name in profile.expense_categories
        ]

        for name, category_type in planned:
            try:
                created.append(
                    await self._category_repository.create(name=name, type=category_type)
                )
            except ConflictError:
                # Já existe (empresa antiga ou semeadura repetida) — segue.
                continue
        return created
