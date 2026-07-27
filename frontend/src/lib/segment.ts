import type { SegmentProfileResponse } from "@/lib/api-types";

/**
 * Espelho do perfil genérico do backend. Serve de fallback enquanto o perfil real
 * carrega — mantém a tela utilizável sem piscar rótulos errados.
 */
export const GENERIC_SEGMENT_PROFILE: SegmentProfileResponse = {
  id: "generic",
  label: "Negócio",
  offering: "both",
  modules: ["clients", "services", "products", "employees"],
  terminology: {
    clients: "Clientes",
    client_singular: "cliente",
    catalog: "Produtos & Serviços",
    products: "Produtos",
    services: "Serviços",
    employees: "Funcionários",
    employee_singular: "funcionário",
    agenda: "Agenda",
    appointment_singular: "agendamento",
    transactions: "Lançamentos",
  },
  catalog_fields: {
    sku: true,
    barcode: true,
    brand: true,
    supplier: true,
    variants: true,
    inventory: true,
    duration: false,
  },
  service_examples: [],
  product_examples: [],
  catalog_categories: [],
  employee_role_examples: [],
  income_categories: ["Vendas", "Serviços"],
  expense_categories: ["Fornecedores", "Aluguel", "Salários", "Impostos", "Marketing"],
  kpis: ["total_revenue", "total_expenses", "profit", "active_clients"],
  integrations: [],
  capabilities: [],
  sells_products: true,
  sells_services: true,
};

/** Monta um placeholder "Ex.: A, B" a partir dos exemplos reais do segmento. */
export function exampleHint(examples: string[], limit = 2): string | undefined {
  if (examples.length === 0) {
    return undefined;
  }
  return `Ex.: ${examples.slice(0, limit).join(", ")}`;
}

/** Recursos do produto que só fazem sentido em certos negócios (espelha o
 * Capability do backend — vocabulário fechado, sem string solta nas telas). */
export const CAPABILITY = {
  clientRetention: "client_retention",
  inventory: "inventory",
  salesChannels: "sales_channels",
  productMargin: "product_margin",
  commissions: "commissions",
  scheduleAnalytics: "schedule_analytics",
  recurringRevenue: "recurring_revenue",
} as const;

export type CapabilityId = (typeof CAPABILITY)[keyof typeof CAPABILITY];

export function hasCapability(
  profile: { capabilities: string[] },
  capability: CapabilityId,
): boolean {
  return profile.capabilities.includes(capability);
}
