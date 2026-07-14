import { motion } from "framer-motion";
import {
  ArrowDownRight,
  ArrowUpRight,
  LayoutDashboard,
  Minus,
  Receipt,
  Sparkles,
  TrendingDown,
  TrendingUp,
  Users,
  Wallet,
} from "lucide-react";
import { useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { EmptyState } from "@/components/empty-state";
import { AskCard, SummaryCard } from "@/features/dashboard/ai-panel";
import { InsightsCard } from "@/features/dashboard/insights-card";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { useDashboard } from "@/features/dashboard/use-dashboard";
import { useCompanyCurrency } from "@/features/companies/use-company-currency";
import type { CategoryBreakdownResponse, ComputedKPIResponse } from "@/lib/api-types";
import { cn, formatCents, formatPercent } from "@/lib/utils";

type PeriodKey = "this_month" | "last_30" | "last_90" | "this_year";

const PERIOD_LABELS: Record<PeriodKey, string> = {
  this_month: "Este mês",
  last_30: "Últimos 30 dias",
  last_90: "Últimos 90 dias",
  this_year: "Este ano",
};

function periodRange(key: PeriodKey): { start: string; end: string; months: number } {
  const now = new Date();
  const end = now.toISOString();
  switch (key) {
    case "this_month": {
      const start = new Date(now.getFullYear(), now.getMonth(), 1);
      return { start: start.toISOString(), end, months: 6 };
    }
    case "last_30": {
      const start = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
      return { start: start.toISOString(), end, months: 6 };
    }
    case "last_90": {
      const start = new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000);
      return { start: start.toISOString(), end, months: 6 };
    }
    case "this_year": {
      const start = new Date(now.getFullYear(), 0, 1);
      return { start: start.toISOString(), end, months: 12 };
    }
  }
}

const MONTH_LABELS = [
  "jan",
  "fev",
  "mar",
  "abr",
  "mai",
  "jun",
  "jul",
  "ago",
  "set",
  "out",
  "nov",
  "dez",
];

function ChangeIndicator({ change }: { change: number | null }) {
  if (change === null) {
    return (
      <span className="flex items-center gap-1 text-xs text-muted-foreground">
        <Minus className="size-3" /> sem base de comparação
      </span>
    );
  }
  const positive = change > 0;
  return (
    <span
      className={cn(
        "flex items-center gap-1 text-xs font-medium",
        positive ? "text-success" : change < 0 ? "text-destructive" : "text-muted-foreground",
      )}
    >
      {positive ? <ArrowUpRight className="size-3" /> : <ArrowDownRight className="size-3" />}
      {formatPercent(change)} vs. período anterior
    </span>
  );
}

function StatCard({
  title,
  value,
  icon: Icon,
  change,
  tone,
}: {
  title: string;
  value: string;
  icon: React.ComponentType<{ className?: string }>;
  change?: number | null;
  tone?: "positive" | "negative" | "neutral";
}) {
  return (
    <Card>
      <CardContent className="p-5">
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">{title}</p>
          <div
            className={cn(
              "flex size-8 items-center justify-center rounded-md",
              tone === "positive" && "bg-success/10 text-success",
              tone === "negative" && "bg-destructive/10 text-destructive",
              (tone === "neutral" || tone === undefined) && "bg-primary/10 text-primary",
            )}
          >
            <Icon className="size-4" />
          </div>
        </div>
        <p className="mt-2 text-2xl font-semibold tracking-tight">{value}</p>
        {change !== undefined && (
          <div className="mt-1">
            <ChangeIndicator change={change} />
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function formatKPIValue(kpi: ComputedKPIResponse, currency: string): string {
  switch (kpi.unit) {
    case "cents":
      return formatCents(kpi.value, currency);
    case "percentage":
      return `${kpi.value.toFixed(1).replace(".", ",")}%`;
    case "count":
      return new Intl.NumberFormat("pt-BR").format(kpi.value);
  }
}

function CategoryBars({
  items,
  tone,
  currency,
}: {
  items: CategoryBreakdownResponse[];
  tone: "income" | "expense";
  currency: string;
}) {
  const max = Math.max(...items.map((i) => i.total_cents), 1);
  if (items.length === 0) {
    return <p className="text-sm text-muted-foreground">Nenhum lançamento no período.</p>;
  }
  return (
    <div className="space-y-3">
      {items.map((item) => (
        <div key={item.category_id}>
          <div className="mb-1 flex items-center justify-between text-sm">
            <span className="truncate">{item.category_name}</span>
            <span className="ml-2 shrink-0 font-medium">
              {formatCents(item.total_cents, currency)}
            </span>
          </div>
          <div className="h-2 overflow-hidden rounded-full bg-muted">
            <div
              className={cn(
                "h-full rounded-full",
                tone === "income" ? "bg-success" : "bg-destructive",
              )}
              style={{ width: `${(item.total_cents / max) * 100}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

export function DashboardPage() {
  const { companyId } = useParams<{ companyId: string }>();
  const [period, setPeriod] = useState<PeriodKey>("this_month");
  const currency = useCompanyCurrency(companyId ?? "");
  const range = useMemo(() => periodRange(period), [period]);
  const { data, isLoading } = useDashboard(companyId ?? "", range);

  const chartData = useMemo(
    () =>
      (data?.monthly_breakdown ?? []).map((item) => ({
        name: `${MONTH_LABELS[item.month - 1]}/${String(item.year).slice(2)}`,
        Receita: item.revenue_cents / 100,
        Despesa: item.expense_cents / 100,
        Lucro: item.profit_cents / 100,
      })),
    [data],
  );

  const isEmpty = !isLoading && data !== undefined && data.transaction_count === 0;

  return (
    <div className="mx-auto w-full max-w-6xl px-4 py-8">
      <PageHeader title="Dashboard" description="Visão financeira do período.">
        <Select value={period} onValueChange={(value) => setPeriod(value as PeriodKey)}>
          <SelectTrigger className="w-44" aria-label="Período">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {(Object.keys(PERIOD_LABELS) as PeriodKey[]).map((key) => (
              <SelectItem key={key} value={key}>
                {PERIOD_LABELS[key]}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </PageHeader>

      {isLoading && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
      )}

      {isEmpty && (
        <EmptyState
          icon={LayoutDashboard}
          title="Sem lançamentos no período"
          description="Registre receitas e despesas no módulo financeiro para ver seus indicadores aqui."
        >
          <Button asChild size="sm">
            <Link to={`/c/${companyId}/transactions`}>
              <Wallet /> Ir para o financeiro
            </Link>
          </Button>
        </EmptyState>
      )}

      {data && !isEmpty && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25 }}
          className="space-y-6"
        >
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard
              title="Receita"
              value={formatCents(data.revenue_cents, currency)}
              icon={TrendingUp}
              change={data.comparison.revenue_change_pct}
              tone="positive"
            />
            <StatCard
              title="Despesas"
              value={formatCents(data.expense_cents, currency)}
              icon={TrendingDown}
              change={data.comparison.expense_change_pct}
              tone="negative"
            />
            <StatCard
              title="Lucro"
              value={formatCents(data.profit_cents, currency)}
              icon={Wallet}
              change={data.comparison.profit_change_pct}
              tone={data.profit_cents >= 0 ? "positive" : "negative"}
            />
            <StatCard
              title="Clientes ativos"
              value={new Intl.NumberFormat("pt-BR").format(data.active_clients)}
              icon={Users}
              tone="neutral"
            />
          </div>

          {data.kpis.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Sparkles className="size-4 text-primary" /> Indicadores do seu negócio
                </CardTitle>
              </CardHeader>
              <CardContent className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {data.kpis.map((kpi) => (
                  <div key={kpi.key} className="rounded-lg border p-4">
                    <p className="text-sm text-muted-foreground">{kpi.name}</p>
                    <p className="mt-1 text-xl font-semibold tracking-tight">
                      {formatKPIValue(kpi, currency)}
                    </p>
                    <p className="mt-1 text-xs text-muted-foreground">{kpi.description}</p>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          <InsightsCard companyId={companyId ?? ""} start={range.start} end={range.end} />

          <div className="grid gap-6 lg:grid-cols-2">
            <SummaryCard companyId={companyId ?? ""} start={range.start} end={range.end} />
            <AskCard companyId={companyId ?? ""} start={range.start} end={range.end} />
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Receipt className="size-4 text-primary" /> Evolução mensal
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-72 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData} margin={{ top: 4, right: 8, bottom: 0, left: 8 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                    <XAxis
                      dataKey="name"
                      tick={{ fill: "var(--color-muted-foreground)", fontSize: 12 }}
                      axisLine={false}
                      tickLine={false}
                    />
                    <YAxis
                      tick={{ fill: "var(--color-muted-foreground)", fontSize: 12 }}
                      axisLine={false}
                      tickLine={false}
                      tickFormatter={(value: number) =>
                        new Intl.NumberFormat("pt-BR", {
                          notation: "compact",
                          maximumFractionDigits: 1,
                        }).format(value)
                      }
                    />
                    <Tooltip
                      formatter={(value: number | string) =>
                        formatCents(Math.round(Number(value) * 100), currency)
                      }
                      contentStyle={{
                        backgroundColor: "var(--color-popover)",
                        border: "1px solid var(--color-border)",
                        borderRadius: "0.5rem",
                        color: "var(--color-popover-foreground)",
                      }}
                    />
                    <Legend wrapperStyle={{ fontSize: 12 }} />
                    <Bar dataKey="Receita" fill="var(--color-success)" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="Despesa" fill="var(--color-destructive)" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="Lucro" fill="var(--color-primary)" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          <div className="grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Principais receitas</CardTitle>
              </CardHeader>
              <CardContent>
                <CategoryBars
                  items={data.top_income_categories}
                  tone="income"
                  currency={currency}
                />
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Principais despesas</CardTitle>
              </CardHeader>
              <CardContent>
                <CategoryBars
                  items={data.top_expense_categories}
                  tone="expense"
                  currency={currency}
                />
              </CardContent>
            </Card>
          </div>
        </motion.div>
      )}
    </div>
  );
}
