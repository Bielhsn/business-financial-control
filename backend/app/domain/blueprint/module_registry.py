from dataclasses import dataclass


@dataclass(frozen=True)
class ModuleDefinition:
    id: str
    name: str
    description: str


MODULE_REGISTRY: tuple[ModuleDefinition, ...] = (
    ModuleDefinition(
        "financial_core",
        "Financeiro",
        "Fluxo de caixa, contas a pagar e a receber, categorias financeiras.",
    ),
    ModuleDefinition(
        "dashboard", "Dashboard Financeiro", "Indicadores, gráficos e KPIs consolidados."
    ),
    ModuleDefinition(
        "clients", "Clientes", "Cadastro de clientes com histórico de atendimentos/compras."
    ),
    ModuleDefinition("products", "Produtos", "Catálogo de produtos vendidos."),
    ModuleDefinition("services", "Serviços", "Catálogo de serviços oferecidos."),
    ModuleDefinition("inventory", "Estoque", "Controle de estoque de produtos."),
    ModuleDefinition("employees", "Funcionários", "Cadastro de funcionários e prestadores."),
    ModuleDefinition("appointments", "Agenda", "Agendamento de horários e atendimentos."),
    ModuleDefinition("projects", "Projetos", "Gestão de projetos e custos por projeto."),
    ModuleDefinition("contracts", "Contratos", "Contratos firmados com clientes."),
    ModuleDefinition("recurring_revenue", "Receita Recorrente", "Assinaturas e mensalidades."),
)

MODULE_IDS: frozenset[str] = frozenset(module.id for module in MODULE_REGISTRY)


def get_module(module_id: str) -> ModuleDefinition | None:
    return next((module for module in MODULE_REGISTRY if module.id == module_id), None)
