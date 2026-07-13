import { useQuery } from "@tanstack/react-query";
import { Bell } from "lucide-react";
import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useCompanyCurrency } from "@/features/companies/use-company-currency";
import { api } from "@/lib/api";
import { cn, formatCents } from "@/lib/utils";

interface NotificationItem {
  kind: "overdue" | "due_soon";
  transaction_id: string;
  description: string;
  amount_cents: number;
  type: "income" | "expense";
  due_date: string;
}

function useNotifications(companyId: string) {
  return useQuery({
    queryKey: ["companies", companyId, "notifications"],
    queryFn: async () => {
      const { data } = await api.get<NotificationItem[]>(`/companies/${companyId}/notifications`);
      return data;
    },
    staleTime: 60_000,
    refetchInterval: 120_000,
  });
}

export function NotificationsBell({ companyId }: { companyId: string }) {
  const { data: notifications } = useNotifications(companyId);
  const currency = useCompanyCurrency(companyId);
  const count = notifications?.length ?? 0;
  const overdueCount = notifications?.filter((n) => n.kind === "overdue").length ?? 0;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="relative"
          aria-label={count === 0 ? "Notificações" : `Notificações: ${count} conta(s) a vencer`}
        >
          <Bell />
          {count > 0 && (
            <span
              className={cn(
                "absolute -right-0.5 -top-0.5 flex size-4 items-center justify-center rounded-full text-[10px] font-semibold text-white",
                overdueCount > 0 ? "bg-destructive" : "bg-primary",
              )}
            >
              {count > 9 ? "9+" : count}
            </span>
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-80">
        <DropdownMenuLabel>Contas a pagar e receber</DropdownMenuLabel>
        <DropdownMenuSeparator />
        {count === 0 && (
          <p className="px-2 py-3 text-sm text-muted-foreground">
            Nada vencido nem vencendo nos próximos 7 dias. 🎉
          </p>
        )}
        {(notifications ?? []).slice(0, 6).map((notification) => (
          <DropdownMenuItem key={notification.transaction_id} asChild>
            <Link to={`/c/${companyId}/transactions`} className="flex items-start gap-2">
              <span
                className={cn(
                  "mt-1 size-2 shrink-0 rounded-full",
                  notification.kind === "overdue" ? "bg-destructive" : "bg-primary",
                )}
              />
              <span className="min-w-0 flex-1">
                <span className="block truncate text-sm">{notification.description}</span>
                <span className="block text-xs text-muted-foreground">
                  {notification.kind === "overdue" ? "Venceu em " : "Vence em "}
                  {new Date(notification.due_date).toLocaleDateString("pt-BR")} ·{" "}
                  {formatCents(notification.amount_cents, currency)}
                </span>
              </span>
            </Link>
          </DropdownMenuItem>
        ))}
        {count > 6 && (
          <>
            <DropdownMenuSeparator />
            <DropdownMenuItem asChild>
              <Link to={`/c/${companyId}/transactions`} className="justify-center text-sm">
                Ver todas ({count})
              </Link>
            </DropdownMenuItem>
          </>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
