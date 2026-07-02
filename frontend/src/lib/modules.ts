/** Espelha o MODULE_REGISTRY do backend (backend/app/domain/blueprint/module_registry.py). */

export interface ModuleInfo {
  id: string;
  label: string;
  description: string;
}

export const MODULES: ModuleInfo[] = [
  {
    id: "financial_core",
    label: "Financeiro",
    description: "Fluxo de caixa, contas a pagar e a receber, categorias financeiras.",
  },
  {
    id: "dashboard",
    label: "Dashboard Financeiro",
    description: "Indicadores, gráficos e KPIs consolidados.",
  },
  {
    id: "clients",
    label: "Clientes",
    description: "Cadastro de clientes com histórico de atendimentos/compras.",
  },
  { id: "products", label: "Produtos", description: "Catálogo de produtos vendidos." },
  { id: "services", label: "Serviços", description: "Catálogo de serviços oferecidos." },
  { id: "inventory", label: "Estoque", description: "Controle de estoque de produtos." },
  {
    id: "employees",
    label: "Funcionários",
    description: "Cadastro de funcionários e prestadores.",
  },
  {
    id: "appointments",
    label: "Agenda",
    description: "Agendamento de horários e atendimentos.",
  },
  {
    id: "projects",
    label: "Projetos",
    description: "Gestão de projetos e custos por projeto.",
  },
  { id: "contracts", label: "Contratos", description: "Contratos firmados com clientes." },
  {
    id: "recurring_revenue",
    label: "Receita Recorrente",
    description: "Assinaturas e mensalidades.",
  },
];

export function moduleLabel(id: string): string {
  return MODULES.find((m) => m.id === id)?.label ?? id;
}

export function moduleDescription(id: string): string {
  return MODULES.find((m) => m.id === id)?.description ?? "";
}
