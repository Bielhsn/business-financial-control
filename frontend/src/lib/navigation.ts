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

/** Módulos padrão quando não há blueprint nem segmento reconhecido: básicos que
 * não travam o produto (Clientes, Produtos & Serviços, Funcionários). */
const DEFAULT_MODULES = ["clients", "services", "employees"];

interface SegmentPreset {
  /** Radicais em minúsculo e SEM acento (o segmento é normalizado antes de casar). */
  keywords: string[];
  modules: string[];
}

/**
 * Presets de módulos por segmento — usados quando a empresa ainda não gerou o
 * blueprint por IA, para a sidebar já refletir o tipo de negócio. Só ativam
 * módulos com página real (nada "em construção"). O primeiro preset que casar vence.
 */
const SEGMENT_PRESETS: SegmentPreset[] = [
  {
    // Beleza e cuidados pessoais.
    keywords: [
      "barbear",
      "barber",
      "cabelele",
      "cabeleire",
      "salao",
      "beleza",
      "estetic",
      "manicure",
      "pedicure",
      "unha",
      "spa",
      "maquiag",
      "sobrancelha",
      "depilac",
      "tatuag",
    ],
    modules: ["clients", "services", "employees", "appointments"],
  },
  {
    // Saúde e clínicas (inclui laboratórios de imuno/hematologia).
    keywords: [
      "clinic",
      "laborator",
      "imuno",
      "hemato",
      "saude",
      "medic",
      "odonto",
      "dent",
      "fisioter",
      "psico",
      "veterin",
      "exame",
      "diagnostic",
      "nutric",
      "consultorio",
    ],
    modules: ["clients", "services", "employees", "appointments"],
  },
  {
    // Academias, estúdios e fitness.
    keywords: [
      "academia",
      "fitness",
      "crossfit",
      "pilates",
      "yoga",
      "personal",
      "musculac",
      "estudio",
      "danca",
      "luta",
    ],
    modules: ["clients", "services", "employees", "appointments"],
  },
  {
    // Alimentação e food service.
    keywords: [
      "restaurant",
      "lanchon",
      "food",
      "bar",
      "pizzar",
      "hambur",
      "cafeter",
      "padaria",
      "confeitar",
      "acai",
      "sorveter",
      "delivery",
      "comida",
      "gastro",
      "marmit",
    ],
    modules: ["clients", "products", "inventory", "employees"],
  },
  {
    // Varejo e comércio.
    keywords: [
      "loja",
      "varejo",
      "comercio",
      "boutique",
      "roupa",
      "moda",
      "vestuar",
      "calcad",
      "mercado",
      "mercear",
      "papelaria",
      "petshop",
      "pet shop",
      "farmacia",
      "otica",
      "distribuidora",
    ],
    modules: ["clients", "products", "inventory"],
  },
  {
    // Serviços profissionais e consultorias.
    keywords: [
      "consultor",
      "advocacia",
      "advog",
      "contabil",
      "juridic",
      "agencia",
      "marketing",
      "arquitet",
      "engenh",
      "design",
      "software",
      "tecnologia",
      "assessoria",
    ],
    modules: ["clients", "services", "employees"],
  },
];

/** Remove acentos e baixa a caixa para casar segmentos digitados livremente. */
function normalize(text: string): string {
  return text.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
}

/**
 * Deriva os módulos a partir do segmento livre da empresa (fallback sem blueprint).
 * Nunca retorna vazio: sem correspondência, usa os módulos padrão.
 */
export function modulesForSegment(segment: string | null): string[] {
  if (segment) {
    const normalized = normalize(segment);
    const preset = SEGMENT_PRESETS.find((candidate) =>
      candidate.keywords.some((keyword) => normalized.includes(keyword)),
    );
    if (preset) {
      return preset.modules;
    }
  }
  return DEFAULT_MODULES;
}

/**
 * Deriva a navegação visível. Com blueprint, é o retrato exato do que a IA ativou;
 * sem blueprint, cai nos presets por `segment` para a sidebar já refletir o negócio.
 */
export function visibleNavItems(
  blueprintModules: string[] | null,
  segment: string | null = null,
): NavItem[] {
  const modules = blueprintModules ?? modulesForSegment(segment);
  return NAV_ITEMS.filter((item) => {
    if (item.always) {
      return true;
    }
    return item.modules.some((moduleId) => modules.includes(moduleId));
  });
}
