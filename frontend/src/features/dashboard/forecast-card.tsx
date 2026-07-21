import { TrendingDown, TrendingUp } from "lucide-react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useCashflowForecast } from "@/features/dashboard/use-forecast";
import type { CashflowForecastResponse } from "@/lib/api-types";
import { cn, formatCents } from "@/lib/utils";

const MONTH_NAMES = [
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

export function ForecastCard({ companyId }: { companyId: string }) {
  const { data, isLoading } = useCashflowForecast(companyId);

  if (isLoading) {
    return <Skeleton className="h-56 w-full" />;
  }
  if (!data) {
    return null;
  }

  const hasHistory = data.history.some(
    (point) => point.income_cents > 0 || point.expense_cents > 0,
  );
  // Sem histórico nem movimento no mês, a previsão não diz nada útil.
  if (!hasHistory && data.current_month_actual_net_cents === 0) {
    return null;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Previsão de fluxo de caixa</CardTitle>
        <CardDescription>
          Projeção do resultado (receitas − despesas) com base no ritmo atual e nos meses
          anteriores.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-5">
        <div className="grid gap-4 sm:grid-cols-3">
          <Projection label="Mês atual (realizado)" value={data.current_month_actual_net_cents} />
          <Projection
            label="Mês atual (projetado)"
            value={data.current_month_projected_net_cents}
            highlight
          />
          <Projection label="Próximo mês (projeção)" value={data.next_month_projected_net_cents} />
        </div>

        {data.trend_pct !== null && <Trend pct={data.trend_pct} />}

        <HistoryChart data={data} />
        <p className="text-xs text-muted-foreground">Método: {data.method}.</p>
      </CardContent>
    </Card>
  );
}

function Projection({
  label,
  value,
  highlight,
}: {
  label: string;
  value: number;
  highlight?: boolean;
}) {
  return (
    <div className={cn("rounded-lg border p-3", highlight && "border-primary bg-primary/5")}>
      <p className="text-xs text-muted-foreground">{label}</p>
      <p
        className={cn(
          "text-lg font-semibold tracking-tight",
          value < 0 ? "text-destructive" : "text-foreground",
        )}
      >
        {formatCents(value)}
      </p>
    </div>
  );
}

function Trend({ pct }: { pct: number }) {
  const positive = pct >= 0;
  return (
    <div
      className={cn(
        "flex items-center gap-2 text-sm",
        positive ? "text-success" : "text-destructive",
      )}
    >
      {positive ? <TrendingUp className="size-4" /> : <TrendingDown className="size-4" />}
      <span>
        Tendência {positive ? "de alta" : "de queda"} de {Math.abs(pct)}% no período analisado.
      </span>
    </div>
  );
}

function HistoryChart({ data }: { data: CashflowForecastResponse }) {
  const points = [
    ...data.history,
    {
      year: 0,
      month: 0,
      income_cents: 0,
      expense_cents: 0,
      net_cents: data.current_month_projected_net_cents,
    },
  ];
  const max = Math.max(1, ...points.map((p) => Math.abs(p.net_cents)));

  return (
    <div className="flex items-end gap-2" style={{ height: 96 }}>
      {points.map((point, index) => {
        const isForecast = index === points.length - 1;
        const heightPct = Math.round((Math.abs(point.net_cents) / max) * 100);
        const negative = point.net_cents < 0;
        return (
          <div key={index} className="flex flex-1 flex-col items-center gap-1">
            <div className="flex w-full flex-1 items-end">
              <div
                className={cn(
                  "w-full rounded-t",
                  isForecast ? "bg-primary/40" : negative ? "bg-destructive/60" : "bg-primary",
                )}
                style={{ height: `${Math.max(heightPct, 4)}%` }}
                title={formatCents(point.net_cents)}
              />
            </div>
            <span className="text-[10px] text-muted-foreground">
              {isForecast ? "prev." : MONTH_NAMES[point.month - 1]}
            </span>
          </div>
        );
      })}
    </div>
  );
}
