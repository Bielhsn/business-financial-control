import { AlertTriangle, ArrowLeft, Building2, Plug, TrendingUp, Users } from "lucide-react";
import { Link, Navigate } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useAdminOverview, useIsPlatformAdmin } from "@/features/admin/use-admin";
import type { PlanTier } from "@/lib/api-types";
import { cn, formatCents } from "@/lib/utils";

const PLAN_LABELS: Record<PlanTier, string> = {
  starter: "Starter",
  professional: "Professional",
  business: "Business",
  enterprise: "Enterprise",
};

const STATUS_LABELS: Record<string, string> = {
  trialing: "Em teste",
  active: "Ativas",
  past_due: "Inadimplentes",
  canceled: "Canceladas",
};

export function AdminDashboardPage() {
  const { data: isAdmin, isLoading: checkingAdmin } = useIsPlatformAdmin();
  const { data: overview, isLoading } = useAdminOverview(isAdmin === true);

  if (checkingAdmin) {
    return (
      <div className="mx-auto w-full max-w-6xl px-4 py-10">
        <Skeleton className="h-40 w-full" />
      </div>
    );
  }

  if (isAdmin === false) {
    return <Navigate to="/companies" replace />;
  }

  return (
    <div className="mx-auto w-full max-w-6xl px-4 py-10">
      <div className="mb-8 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Painel administrativo</h1>
          <p className="text-sm text-muted-foreground">
            Visão geral da plataforma Aurum OS — receita, clientes e saúde do sistema.
          </p>
        </div>
        <Button asChild variant="outline">
          <Link to="/companies">
            <ArrowLeft /> Voltar
          </Link>
        </Button>
      </div>

      {isLoading || !overview ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[0, 1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-28" />
          ))}
        </div>
      ) : (
        <div className="space-y-6">
          <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatTile
              icon={<TrendingUp className="size-4" />}
              label="MRR"
              value={formatCents(overview.revenue.mrr_cents)}
              hint={`ARR ${formatCents(overview.revenue.arr_cents)}`}
            />
            <StatTile
              icon={<Users className="size-4" />}
              label="Clientes ativos"
              value={String(overview.customers.active_companies)}
              hint={`${overview.customers.new_this_month} novos este mês`}
            />
            <StatTile
              icon={<AlertTriangle className="size-4" />}
              label="Churn"
              value={`${overview.customers.churn_rate_pct}%`}
              hint={`${overview.customers.churned} cancelamentos`}
              warning={overview.customers.churn_rate_pct >= 10}
            />
            <StatTile
              icon={<Building2 className="size-4" />}
              label="Assinaturas pagas"
              value={String(overview.revenue.active_paying)}
              hint={`${overview.revenue.trials} em teste`}
            />
          </section>

          <div className="grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Assinaturas por plano</CardTitle>
                <CardDescription>Assinantes e MRR de cada nível.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {overview.subscriptions.by_plan.map((plan) => (
                  <div key={plan.tier} className="flex items-center justify-between text-sm">
                    <span className="font-medium">{PLAN_LABELS[plan.tier]}</span>
                    <span className="text-muted-foreground">
                      {plan.subscribers} assinante(s) · {formatCents(plan.mrr_cents)}/mês
                    </span>
                  </div>
                ))}
                <div className="flex flex-wrap gap-2 border-t pt-3">
                  {Object.entries(overview.subscriptions.by_status).map(([status, count]) => (
                    <Badge key={status} variant={status === "past_due" ? "warning" : "muted"}>
                      {STATUS_LABELS[status] ?? status}: {count}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Empresas por segmento</CardTitle>
                <CardDescription>Onde estão concentrados os clientes.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                {overview.segments.length === 0 && (
                  <p className="text-sm text-muted-foreground">Nenhuma empresa cadastrada ainda.</p>
                )}
                {overview.segments.map((segment) => (
                  <SegmentBar
                    key={segment.segment}
                    label={segment.segment}
                    count={segment.company_count}
                    total={overview.customers.total_companies}
                  />
                ))}
              </CardContent>
            </Card>
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Volume na plataforma</CardTitle>
                <CardDescription>
                  Total transacionado pelas empresas (não é a receita do SaaS).
                </CardDescription>
              </CardHeader>
              <CardContent className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-muted-foreground">Receitas lançadas</p>
                  <p className="text-lg font-semibold text-success">
                    {formatCents(overview.revenue.platform_gmv_cents)}
                  </p>
                </div>
                <div>
                  <p className="text-muted-foreground">Despesas lançadas</p>
                  <p className="text-lg font-semibold text-destructive">
                    {formatCents(overview.revenue.platform_expenses_cents)}
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Sistema</CardTitle>
                <CardDescription>Uso e integrações da plataforma.</CardDescription>
              </CardHeader>
              <CardContent className="grid grid-cols-2 gap-4 text-sm">
                <SystemStat
                  label="Usuários"
                  value={overview.system.total_users}
                  icon={<Users className="size-4" />}
                />
                <SystemStat
                  label="Empresas"
                  value={overview.system.total_companies}
                  icon={<Building2 className="size-4" />}
                />
                <SystemStat
                  label="Integrações"
                  value={overview.system.total_connections}
                  icon={<Plug className="size-4" />}
                />
                <SystemStat
                  label="Integrações com erro"
                  value={overview.system.connections_with_error}
                  icon={<AlertTriangle className="size-4" />}
                  warning={overview.system.connections_with_error > 0}
                />
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}

function StatTile({
  icon,
  label,
  value,
  hint,
  warning,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  hint?: string;
  warning?: boolean;
}) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="mb-1 flex items-center gap-2 text-sm text-muted-foreground">
          {icon}
          {label}
        </div>
        <p className={cn("text-2xl font-bold tracking-tight", warning && "text-warning")}>
          {value}
        </p>
        {hint && <p className="text-xs text-muted-foreground">{hint}</p>}
      </CardContent>
    </Card>
  );
}

function SegmentBar({ label, count, total }: { label: string; count: number; total: number }) {
  const pct = total > 0 ? Math.round((count / total) * 100) : 0;
  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-sm">
        <span>{label}</span>
        <span className="text-muted-foreground">
          {count} ({pct}%)
        </span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-muted">
        <div className="h-full rounded-full bg-primary" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

function SystemStat({
  label,
  value,
  icon,
  warning,
}: {
  label: string;
  value: number;
  icon: React.ReactNode;
  warning?: boolean;
}) {
  return (
    <div className="flex items-center gap-3">
      <div
        className={cn(
          "flex size-9 items-center justify-center rounded-lg bg-accent text-accent-foreground",
          warning && "bg-warning/15 text-warning",
        )}
      >
        {icon}
      </div>
      <div>
        <p className={cn("text-lg font-semibold", warning && "text-warning")}>{value}</p>
        <p className="text-xs text-muted-foreground">{label}</p>
      </div>
    </div>
  );
}
