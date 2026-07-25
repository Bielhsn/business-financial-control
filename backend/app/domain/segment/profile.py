"""Perfil de segmento — o contrato que descreve COMO um tipo de negócio usa a
plataforma.

Antes desta camada, a adaptação por segmento dependia do blueprint gerado por IA
(que exige chave configurada, uma ação manual do dono e não é determinístico) ou
de listas de palavra-chave soltas no frontend. O resultado era um painel genérico:
uma barbearia via o formulário de catálogo pedindo SKU e código de barras para um
corte de cabelo, com exemplos de loja de roupas.

Aqui o segmento vira **regra de negócio**: uma estrutura de dados declarativa que
diz quais módulos existem, como as coisas se chamam, quais campos fazem sentido,
quais categorias financeiras nascem com a empresa e quais indicadores importam.
Adicionar um segmento novo = adicionar um registro no catálogo, sem `if` espalhado
pelo código.
"""

from dataclasses import dataclass, field
from enum import StrEnum

from app.domain.dashboard.kpi_registry import KPIMetric


class OfferingModel(StrEnum):
    """Como o negócio ganha dinheiro. Define o eixo da experiência: uma barbearia
    vive de serviços agendados; uma loja de bebidas, de produtos com estoque."""

    SERVICES = "services"
    PRODUCTS = "products"
    BOTH = "both"


@dataclass(frozen=True)
class CatalogFieldPolicy:
    """Quais campos da ficha de item fazem sentido neste segmento.

    Um serviço não tem código de barras nem fornecedor; um vinho tem os dois, mais
    validade. O frontend usa isso para esconder campo que não se aplica, em vez de
    mostrar a ficha inteira para todo mundo.
    """

    sku: bool = True
    barcode: bool = True
    brand: bool = True
    supplier: bool = True
    variants: bool = True
    inventory: bool = True
    duration: bool = False  # duração do serviço (min) — agenda/atendimento


@dataclass(frozen=True)
class SegmentTerminology:
    """Como o negócio chama as coisas. Uma clínica atende *pacientes*, uma academia
    tem *alunos*, um restaurante tem *cardápio*. Trocar o rótulo é o sinal mais
    barato e mais visível de que o sistema entende o negócio."""

    clients: str = "Clientes"
    client_singular: str = "cliente"
    catalog: str = "Produtos & Serviços"
    products: str = "Produtos"
    services: str = "Serviços"
    employees: str = "Funcionários"
    employee_singular: str = "funcionário"
    agenda: str = "Agenda"
    appointment_singular: str = "agendamento"


@dataclass(frozen=True)
class SegmentProfile:
    """Retrato completo de um tipo de negócio dentro da plataforma."""

    id: str
    label: str
    # Radicais em minúsculo e SEM acento — o texto livre do cadastro é
    # normalizado antes de casar. O primeiro perfil que casar vence.
    keywords: tuple[str, ...]
    offering: OfferingModel
    modules: tuple[str, ...]
    terminology: SegmentTerminology = field(default_factory=SegmentTerminology)
    catalog_fields: CatalogFieldPolicy = field(default_factory=CatalogFieldPolicy)
    # Exemplos reais do segmento — viram placeholders e sugestões de cadastro.
    service_examples: tuple[str, ...] = ()
    product_examples: tuple[str, ...] = ()
    catalog_categories: tuple[str, ...] = ()
    # Categorias financeiras que nascem com a empresa (sem depender de IA).
    income_categories: tuple[str, ...] = ()
    expense_categories: tuple[str, ...] = ()
    # Indicadores que importam para este negócio, na ordem de exibição.
    kpis: tuple[KPIMetric, ...] = ()
    integrations: tuple[str, ...] = ()

    @property
    def sells_services(self) -> bool:
        return self.offering in (OfferingModel.SERVICES, OfferingModel.BOTH)

    @property
    def sells_products(self) -> bool:
        return self.offering in (OfferingModel.PRODUCTS, OfferingModel.BOTH)
