import {
  Building2,
  ChevronsUpDown,
  LogOut,
  Moon,
  Receipt,
  Search,
  Settings,
  Sun,
} from "lucide-react";
import { useEffect } from "react";
import { NavLink, Navigate, Outlet, useNavigate, useParams } from "react-router-dom";

import { AurumMark } from "@/components/brand/logo";
import { CommandPalette, openCommandPalette } from "@/components/command-palette";
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
import { NotificationsBell } from "@/features/notifications/notifications-bell";
import { BRAND } from "@/lib/brand";
import { visibleNavItems } from "@/lib/navigation";
import { cn, readableForeground } from "@/lib/utils";

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
  const { theme } = useTheme();

  // Tema padrão da empresa: aplicado apenas a quem segue a preferência do sistema
  // (nunca sobrescreve escolha manual do usuário) e desfeito ao sair do painel.
  const brandTheme = company?.brand_theme ?? null;
  useEffect(() => {
    if (theme !== "system" || brandTheme === null) {
      return;
    }
    const root = document.documentElement;
    const hadDark = root.classList.contains("dark");
    root.classList.toggle("dark", brandTheme === "dark");
    return () => {
      root.classList.toggle("dark", hadDark);
    };
  }, [theme, brandTheme]);

  if (!companyId) {
    return <Navigate to="/companies" replace />;
  }
  if (isError) {
    // Sem vínculo com a empresa (backend devolve 404) — volta para a seleção.
    return <Navigate to="/companies" replace />;
  }

  // Sem blueprint (null) a navegação mostra os módulos operacionais básicos;
  // com blueprint, é o retrato exato do que a IA ativou para o segmento.
  const visibleItems = visibleNavItems(blueprint ? blueprint.modules : null);

  // Cor da marca da empresa: sobrescreve os tokens de primária apenas dentro do shell.
  const brandStyle = company?.brand_primary_color
    ? ({
        "--primary": company.brand_primary_color,
        "--ring": company.brand_primary_color,
        "--primary-foreground": readableForeground(company.brand_primary_color),
      } as React.CSSProperties)
    : undefined;

  return (
    <div className="flex min-h-screen" style={brandStyle}>
      <aside className="hidden w-60 shrink-0 flex-col border-r bg-card md:flex">
        <div className="flex h-14 items-center gap-2 border-b px-4">
          <button
            type="button"
            onClick={() => navigate("/companies")}
            className="flex w-full items-center gap-2 rounded-md px-1 py-1 text-left transition-colors hover:bg-accent"
            aria-label="Trocar de empresa"
          >
            <div className="flex size-7 shrink-0 items-center justify-center overflow-hidden rounded-md bg-primary/10 text-primary">
              {company?.brand_logo ? (
                <img
                  src={company.brand_logo}
                  alt=""
                  aria-hidden="true"
                  className="size-full object-contain"
                />
              ) : (
                <Building2 className="size-4" />
              )}
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
        <div className="space-y-2 border-t p-3 text-xs text-muted-foreground">
          {blueprint ? (
            <p className="flex items-center gap-1.5">
              <Receipt className="size-3.5" />
              Painel adaptado para {company?.segment}
            </p>
          ) : (
            <p>Gere o blueprint com IA para adaptar o painel.</p>
          )}
          <p className="flex items-center gap-1.5 opacity-70">
            <AurumMark className="size-4" />
            {BRAND.product}
          </p>
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
            <Button
              variant="outline"
              size="sm"
              className="hidden gap-2 text-muted-foreground sm:inline-flex"
              onClick={openCommandPalette}
            >
              <Search className="size-3.5" /> Buscar…
              <kbd className="rounded border bg-muted px-1 text-[10px]">⌘K</kbd>
            </Button>
            <NotificationsBell companyId={companyId} />
            <Button
              variant="ghost"
              size="icon"
              aria-label="Configurações da empresa"
              onClick={() => navigate(`/c/${companyId}/settings`)}
            >
              <Settings />
            </Button>
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
        <CommandPalette companyId={companyId} navItems={visibleItems} />
      </div>
    </div>
  );
}
