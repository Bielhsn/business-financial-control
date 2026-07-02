import {
  Building2,
  ChevronsUpDown,
  LayoutDashboard,
  LogOut,
  Moon,
  Package,
  Receipt,
  Sun,
  UserRound,
  Users,
  Wallet,
} from "lucide-react";
import { NavLink, Navigate, Outlet, useNavigate, useParams } from "react-router-dom";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Skeleton } from "@/components/ui/skeleton";
import { useTheme } from "@/components/theme/theme-provider";
import { useCurrentUser, useLogout } from "@/features/auth/use-auth";
import { useBlueprint } from "@/features/blueprint/use-blueprint";
import { useCompany } from "@/features/companies/use-companies";
import { cn } from "@/lib/utils";

interface NavItem {
  to: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  /** Módulos do blueprint que habilitam este item (algum deles). Vazio = sempre visível. */
  modules: string[];
}

const NAV_ITEMS: NavItem[] = [
  { to: "", label: "Dashboard", icon: LayoutDashboard, modules: [] },
  { to: "transactions", label: "Financeiro", icon: Wallet, modules: [] },
  { to: "clients", label: "Clientes", icon: Users, modules: ["clients"] },
  {
    to: "catalog",
    label: "Produtos & Serviços",
    icon: Package,
    modules: ["products", "services", "inventory"],
  },
  { to: "employees", label: "Funcionários", icon: UserRound, modules: ["employees"] },
];

function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme();
  return (
    <Button
      variant="ghost"
      size="icon"
      aria-label="Alternar tema"
      onClick={() => setTheme(resolvedTheme === "dark" ? "light" : "dark")}
    >
      {resolvedTheme === "dark" ? <Sun /> : <Moon />}
    </Button>
  );
}

export function CompanyLayout() {
  const { companyId } = useParams<{ companyId: string }>();
  const navigate = useNavigate();
  const { data: company, isLoading, isError } = useCompany(companyId ?? "");
  const { data: blueprint } = useBlueprint(companyId ?? "");
  const { data: user } = useCurrentUser();
  const logout = useLogout();

  if (!companyId) {
    return <Navigate to="/companies" replace />;
  }
  if (isError) {
    // Sem vínculo com a empresa (backend devolve 404) — volta para a seleção.
    return <Navigate to="/companies" replace />;
  }

  const modules = blueprint?.modules ?? [];
  const visibleItems = NAV_ITEMS.filter(
    (item) => item.modules.length === 0 || item.modules.some((m) => modules.includes(m)),
  );

  return (
    <div className="flex min-h-screen">
      <aside className="hidden w-60 shrink-0 flex-col border-r bg-card md:flex">
        <div className="flex h-14 items-center gap-2 border-b px-4">
          <button
            type="button"
            onClick={() => navigate("/companies")}
            className="flex w-full items-center gap-2 rounded-md px-1 py-1 text-left transition-colors hover:bg-accent"
            aria-label="Trocar de empresa"
          >
            <div className="flex size-7 shrink-0 items-center justify-center rounded-md bg-primary/10 text-primary">
              <Building2 className="size-4" />
            </div>
            {isLoading ? (
              <Skeleton className="h-4 w-28" />
            ) : (
              <span className="truncate text-sm font-medium">{company?.name}</span>
            )}
            <ChevronsUpDown className="ml-auto size-3.5 shrink-0 text-muted-foreground" />
          </button>
        </div>
        <nav className="flex-1 space-y-1 p-3" aria-label="Navegação principal">
          {visibleItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to === "" ? `/c/${companyId}` : `/c/${companyId}/${item.to}`}
              end={item.to === ""}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-accent text-accent-foreground"
                    : "text-muted-foreground hover:bg-accent/60 hover:text-foreground",
                )
              }
            >
              <item.icon className="size-4" />
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="border-t p-3 text-xs text-muted-foreground">
          {blueprint ? (
            <p className="flex items-center gap-1.5">
              <Receipt className="size-3.5" />
              Painel adaptado para {company?.segment}
            </p>
          ) : (
            <p>Gere o blueprint com IA para adaptar o painel.</p>
          )}
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-14 items-center justify-between border-b bg-card px-4">
          <div className="md:hidden">
            <Button variant="ghost" size="sm" onClick={() => navigate("/companies")}>
              <Building2 /> {company?.name ?? "Empresas"}
            </Button>
          </div>
          <div className="hidden md:block" />
          <div className="flex items-center gap-1">
            <ThemeToggle />
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="sm" className="gap-2">
                  <div className="flex size-6 items-center justify-center rounded-full bg-primary/15 text-xs font-semibold text-primary">
                    {(user?.full_name ?? "?").charAt(0).toUpperCase()}
                  </div>
                  <span className="hidden max-w-32 truncate sm:inline">{user?.full_name}</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuLabel className="truncate">{user?.email}</DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onSelect={() => {
                    logout.mutate(undefined, { onSettled: () => navigate("/login") });
                  }}
                >
                  <LogOut /> Sair
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </header>
        <main className="min-w-0 flex-1 bg-background">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
