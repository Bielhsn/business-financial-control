import { Building2, LogOut, Moon, Search, Settings, Sun } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { useTheme } from "@/components/theme/theme-provider";
import { useLogout } from "@/features/auth/use-auth";
import type { NavItem } from "@/lib/navigation";
import { cn } from "@/lib/utils";

interface Command {
  id: string;
  label: string;
  hint?: string;
  icon: React.ComponentType<{ className?: string }>;
  run: () => void;
}

interface CommandPaletteProps {
  companyId: string;
  navItems: NavItem[];
}

const OPEN_EVENT = "aurum:open-command-palette";

/** Abre a paleta de qualquer lugar (ex.: botão de busca no header). */
export function openCommandPalette() {
  window.dispatchEvent(new CustomEvent(OPEN_EVENT));
}

/**
 * Paleta de comandos (Ctrl/Cmd+K): navegação e ações sem tirar a mão do teclado.
 * Implementação própria sobre o Dialog — sem dependência extra.
 */
export function CommandPalette({ companyId, navItems }: CommandPaletteProps) {
  const navigate = useNavigate();
  const logout = useLogout();
  const { resolvedTheme, setTheme } = useTheme();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [highlighted, setHighlighted] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setOpen((current) => !current);
      }
    };
    const onOpenEvent = () => setOpen(true);
    window.addEventListener("keydown", onKeyDown);
    window.addEventListener(OPEN_EVENT, onOpenEvent);
    return () => {
      window.removeEventListener("keydown", onKeyDown);
      window.removeEventListener(OPEN_EVENT, onOpenEvent);
    };
  }, []);

  useEffect(() => {
    if (open) {
      setQuery("");
      setHighlighted(0);
      // Radix foca o content; devolve o foco para o campo de busca.
      requestAnimationFrame(() => inputRef.current?.focus());
    }
  }, [open]);

  const commands = useMemo<Command[]>(() => {
    const navigation = navItems.map((item) => ({
      id: `nav-${item.to || "dashboard"}`,
      label: item.label,
      hint: "Ir para",
      icon: item.icon,
      run: () => navigate(item.to === "" ? `/c/${companyId}` : `/c/${companyId}/${item.to}`),
    }));
    return [
      ...navigation,
      {
        id: "settings",
        label: "Configurações da empresa",
        hint: "Ir para",
        icon: Settings,
        run: () => navigate(`/c/${companyId}/settings`),
      },
      {
        id: "switch-company",
        label: "Trocar de empresa",
        hint: "Ação",
        icon: Building2,
        run: () => navigate("/companies"),
      },
      {
        id: "toggle-theme",
        label: resolvedTheme === "dark" ? "Mudar para tema claro" : "Mudar para tema escuro",
        hint: "Ação",
        icon: resolvedTheme === "dark" ? Sun : Moon,
        run: () => setTheme(resolvedTheme === "dark" ? "light" : "dark"),
      },
      {
        id: "logout",
        label: "Sair da conta",
        hint: "Ação",
        icon: LogOut,
        run: () => logout.mutate(undefined, { onSettled: () => navigate("/login") }),
      },
    ];
  }, [navItems, companyId, navigate, resolvedTheme, setTheme, logout]);

  const filtered = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (normalized === "") {
      return commands;
    }
    return commands.filter((command) => command.label.toLowerCase().includes(normalized));
  }, [commands, query]);

  const execute = (command: Command) => {
    setOpen(false);
    command.run();
  };

  const onInputKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setHighlighted((current) => Math.min(current + 1, filtered.length - 1));
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setHighlighted((current) => Math.max(current - 1, 0));
    } else if (event.key === "Enter") {
      event.preventDefault();
      const command = filtered[highlighted];
      if (command) {
        execute(command);
      }
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent className="top-[30%] gap-0 p-0 sm:max-w-md" aria-describedby={undefined}>
        <DialogTitle className="sr-only">Paleta de comandos</DialogTitle>
        <div className="flex items-center gap-2 border-b px-4">
          <Search className="size-4 shrink-0 text-muted-foreground" />
          <input
            ref={inputRef}
            value={query}
            onChange={(event) => {
              setQuery(event.target.value);
              setHighlighted(0);
            }}
            onKeyDown={onInputKeyDown}
            placeholder="Buscar página ou ação…"
            aria-label="Buscar página ou ação"
            className="h-12 w-full bg-transparent text-sm outline-none placeholder:text-muted-foreground"
          />
          <kbd className="rounded border bg-muted px-1.5 py-0.5 text-[10px] text-muted-foreground">
            ESC
          </kbd>
        </div>
        <ul className="max-h-72 overflow-y-auto p-2" role="listbox" aria-label="Comandos">
          {filtered.length === 0 && (
            <li className="px-3 py-6 text-center text-sm text-muted-foreground">
              Nada encontrado para “{query}”.
            </li>
          )}
          {filtered.map((command, index) => (
            <li key={command.id} role="option" aria-selected={index === highlighted}>
              <button
                type="button"
                onClick={() => execute(command)}
                onMouseEnter={() => setHighlighted(index)}
                className={cn(
                  "flex w-full items-center gap-3 rounded-md px-3 py-2 text-left text-sm transition-colors",
                  index === highlighted
                    ? "bg-accent text-accent-foreground"
                    : "text-foreground hover:bg-accent/60",
                )}
              >
                <command.icon className="size-4 shrink-0 text-muted-foreground" />
                <span className="flex-1">{command.label}</span>
                {command.hint && (
                  <span className="text-xs text-muted-foreground">{command.hint}</span>
                )}
              </button>
            </li>
          ))}
        </ul>
        <div className="border-t px-4 py-2 text-[11px] text-muted-foreground">
          ↑↓ navega · Enter abre · Ctrl/⌘K abre e fecha
        </div>
      </DialogContent>
    </Dialog>
  );
}
