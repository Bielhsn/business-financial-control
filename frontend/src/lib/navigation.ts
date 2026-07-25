import {
  CalendarDays,
  Crown,
  FileText,
  FolderKanban,
  LayoutDashboard,
  Package,
  Plug,
  Repeat,
  UserRound,
  Users,
  Wallet,
  type LucideIcon,
} from "lucide-react";

import type { SegmentTerminology } from "@/lib/api-types";

/** Chave de terminologia: define de onde o rótulo do item vem no perfil do
 * segmento (uma clínica chama Clientes de "Pacientes", Agenda de "Consultas"). */
type TerminologyKey = keyof SegmentTerminology;

export interface NavItem {
  /** Segmento de rota relativo a /c/:companyId ("" = dashboard). */
  to: string;
  label: string;
  icon: LucideIcon;
  /** Módulos que habilitam este item (qualquer um deles). */
  modules: string[];
  /** Itens core aparecem sempre, independentemente do segmento. */
  always?: boolean;
  /** Módulo ainda sem backend próprio — página informativa "em construção". */
  comingSoon?: boolean;
  /** Quando presente, o rótulo vem da terminologia do segmento. */
  terminologyKey?: TerminologyKey;
}

export const NAV_ITEMS: NavItem[] = [
  { to: "", label: "Dashboard", icon: LayoutDashboard, modules: [], always: true },
  { to: "transactions", label: "Financeiro", icon: Wallet, modules: [], always: true },
  {
    to: "clients",
    label: "Clientes",
    icon: Users,
    modules: ["clients"],
    terminologyKey: "clients",
  },
  {
    to: "catalog",
    label: "Produtos & Serviços",
    icon: Package,
    modules: ["products", "services", "inventory"],
    terminologyKey: "catalog",
  },
  {
    to: "employees",
    label: "Funcionários",
    icon: UserRound,
    modules: ["employees"],
    terminologyKey: "employees",
  },
  {
    to: "agenda",
    label: "Agenda",
    icon: CalendarDays,
    modules: ["appointments"],
    terminologyKey: "agenda",
  },
  {
    to: "subscriptions",
    label: "Assinaturas",
    icon: Repeat,
    modules: ["recurring_revenue"],
    comingSoon: true,
  },
  {
    to: "projects",
    label: "Projetos",
    icon: FolderKanban,
    modules: ["projects"],
    comingSoon: true,
  },
  {
    to: "contracts",
    label: "Contratos",
    icon: FileText,
    modules: ["contracts"],
    comingSoon: true,
  },
  { to: "integrations", label: "Integrações", icon: Plug, modules: [], always: true },
  { to: "plans", label: "Plano", icon: Crown, modules: [], always: true },
];

/**
 * Deriva a navegação a partir dos módulos do segmento e renomeia os itens com a
 * terminologia do negócio.
 *
 * Os módulos vêm do backend (perfil do segmento, determinístico) ou do blueprint
 * gerado por IA quando existir — a decisão de qual usar é de quem chama. Não há
 * mais lista de palavra-chave aqui: uma única fonte de verdade evita a sidebar
 * discordar do resto do sistema.
 */
export function visibleNavItems(
  modules: string[],
  terminology?: SegmentTerminology | null,
): NavItem[] {
  return NAV_ITEMS.filter(
    (item) => item.always || item.modules.some((moduleId) => modules.includes(moduleId)),
  ).map((item) =>
    item.terminologyKey && terminology
      ? { ...item, label: terminology[item.terminologyKey] }
      : item,
  );
}
