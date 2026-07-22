import { TrendingDown, TrendingUp } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { useIncomeStatement } from "@/features/dashboard/use-income-statement";
import type { StatementLineResponse } from "@/lib/api-types";
import { formatCents } from "@/lib/utils";

const MONTHS = [
  "janeiro",
  "fevereiro",
  "março",
  "abril",
  "maio",
  "junho",
  "julho",
  "agosto",
  "setembro",
  "outubro",
  "novembro",
  "dezembro",
];

function ChangeBadge({ pct, goodWhenUp }: { pct: number | null; goodWhenUp: boolean }) {
  if (pct === null) return <span className="text-xs text-muted-foreground">—</span>;
  const up = pct >= 0;
  const good = up === goodWhenUp;
  const Icon = up ? TrendingUp : TrendingDown;
  return (
    <span
      className={`inline-flex items-center gap-1 text-xs font-medium ${
        good ? "text-emerald-600" : "text-destructive"
      }`}
    >
      <Icon className="size-3.5" />
      {up ? "+" : ""}
      {pct}% vs mês anterior
    </span>
  );
}

function Lines({ lines }: { lines: StatementLineResponse[] }) {
  if (lines.length === 0) {
    return <p className="text-sm text-muted-foreground">Nenhum lançamento pago.</p>;
  }
  return (
    <ul className="space-y-1 text-sm">
      {lines.slice(0, 5).map((line) => (
        <li key={line.category_id} className="flex justify-between gap-2">
          <span className="truncate text-muted-foreground">{line.category_name}</span>
          <span className="tabular-nums">{formatCents(line.amount_cents)}</span>
        </li>
      ))}
    </ul>
  );
}

export function IncomeStatementCard({ companyId }: { companyId: string }) {
  const { data } = useIncomeStatement(companyId);
  if (!data) return null;

  const { current } = data;
  const monthLabel = `${MONTHS[data.month - 1]} de ${data.year}`;
  const positive = current.net_result_cents >= 0;

  return (
    <Card>
      <CardContent className="space-y-4 p-5">
        <div>
          <h3 className="font-semibold">Resultado do mês (DRE)</h3>
          <p className="text-sm capitalize text-muted-foreground">{monthLabel}</p>
        </div>

        <div className="grid gap-4 sm:grid-cols-3">
          <div>
            <p className="text-sm text-muted-foreground">Receitas</p>
            <p className="text-lg font-semibold tabular-nums text-emerald-600">
              {formatCents(current.total_income_cents)}
            </p>
            <ChangeBadge pct={data.income_change_pct} goodWhenUp={true} />
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Despesas</p>
            <p className="text-lg font-semibold tabular-nums text-destructive">
              {formatCents(current.total_expense_cents)}
            </p>
            <ChangeBadge pct={data.expense_change_pct} goodWhenUp={false} />
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Resultado</p>
            <p
              className={`text-lg font-bold tabular-nums ${
                positive ? "text-emerald-600" : "text-destructive"
              }`}
            >
              {formatCents(current.net_result_cents)}
            </p>
            <ChangeBadge pct={data.net_change_pct} goodWhenUp={true} />
          </div>
        </div>

        <div className="grid gap-4 border-t pt-3 sm:grid-cols-2">
          <div className="space-y-2">
            <p className="text-sm font-medium">Principais receitas</p>
            <Lines lines={current.income_lines} />
          </div>
          <div className="space-y-2">
            <p className="text-sm font-medium">Principais despesas</p>
            <Lines lines={current.expense_lines} />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
