import {
  CalendarDays,
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

export interface NavItem {
  /** Segmento de rota relativo a /c/:companyId ("" = dashboard). */
  to: string;
  label: string;
  icon: LucideIcon;
  /** Módulos do blueprint que habilitam este item (qualquer um deles). */
  modules: string[];
  /** Itens core aparecem sempre, independentemente do blueprint. */
  always?: boolean;
  /** Módulo ainda sem backend próprio — página informativa "em construção". */
  comingSoon?: boolean;
}

export const NAV_ITEMS: NavItem[] = [
  { to: "", label: "Dashboard", icon: LayoutDashboard, modules: [], always: true },
  { to: "transactions", label: "Financeiro", icon: Wallet, modules: [], always: true },
  { to: "clients", label: "Clientes", icon: Users, modules: ["clients"] },
  {
    to: "catalog",
    label: "Produtos & Serviços",
    icon: Package,
    modules: ["products", "services", "inventory"],
  },
  { to: "employees", label: "Funcionários", icon: UserRound, modules: ["employees"] },
  {
    to: "agenda",
    label: "Agenda",
    icon: CalendarDays,
    modules: ["appointments"],
    comingSoon: true,
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
];

/** Itens exibidos quando a empresa ainda não gerou blueprint (IA desligada ou pendente):
 * módulos operacionais básicos ficam disponíveis para o produto não travar sem IA. */
const DEFAULT_WITHOUT_BLUEPRINT = new Set(["clients", "catalog", "employees"]);

/**
 * Deriva a navegação visível a partir dos módulos do blueprint.
 * `blueprintModules === null` significa "sem blueprint gerado".
 */
export function visibleNavItems(blueprintModules: string[] | null): NavItem[] {
  return NAV_ITEMS.filter((item) => {
    if (item.always) {
      return true;
    }
    if (blueprintModules === null) {
      return DEFAULT_WITHOUT_BLUEPRINT.has(item.to);
    }
    return item.modules.some((moduleId) => blueprintModules.includes(moduleId));
  });
}
