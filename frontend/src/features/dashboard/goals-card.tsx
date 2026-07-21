import { Target, Trash2 } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useDeleteGoal, useGoals, useSetGoal } from "@/features/dashboard/use-goals";
import { extractErrorMessage } from "@/lib/api";
import type { GoalMetric, GoalProgressResponse } from "@/lib/api-types";
import { centsToInput, parseCurrencyToCents } from "@/lib/money";
import { cn, formatCents } from "@/lib/utils";

const METRICS: { metric: GoalMetric; label: string; hint: string }[] = [
  { metric: "monthly_income", label: "Faturamento mensal", hint: "Receitas do mês" },
  { metric: "monthly_net", label: "Resultado mensal", hint: "Receitas − despesas" },
];

export function GoalsCard({ companyId }: { companyId: string }) {
  const { data: goals, isLoading } = useGoals(companyId);
  if (isLoading) {
    return null;
  }
  const byMetric = new Map((goals ?? []).map((goal) => [goal.metric, goal]));

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Target className="size-4 text-primary" /> Metas do mês
        </CardTitle>
        <CardDescription>
          Defina metas e acompanhe o realizado e a projeção (no ritmo atual) até o fim do mês.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {METRICS.map(({ metric, label, hint }) => (
          <GoalRow
            key={metric}
            companyId={companyId}
            metric={metric}
            label={label}
            hint={hint}
            goal={byMetric.get(metric)}
          />
        ))}
      </CardContent>
    </Card>
  );
}

function GoalRow({
  companyId,
  metric,
  label,
  hint,
  goal,
}: {
  companyId: string;
  metric: GoalMetric;
  label: string;
  hint: string;
  goal: GoalProgressResponse | undefined;
}) {
  const [editing, setEditing] = useState(false);
  const [value, setValue] = useState(goal ? centsToInput(goal.target_cents) : "");
  const setGoal = useSetGoal(companyId);
  const deleteGoal = useDeleteGoal(companyId);

  const save = () => {
    const cents = parseCurrencyToCents(value);
    if (cents === null || cents <= 0) {
      toast.error("Informe um valor de meta válido.");
      return;
    }
    setGoal.mutate(
      { metric, target_cents: cents },
      {
        onSuccess: () => {
          toast.success(`Meta de ${label.toLowerCase()} salva.`);
          setEditing(false);
        },
        onError: (error) => toast.error(extractErrorMessage(error)),
      },
    );
  };

  if (!goal && !editing) {
    return (
      <div className="flex items-center justify-between gap-2 rounded-lg border p-3">
        <div>
          <p className="text-sm font-medium">{label}</p>
          <p className="text-xs text-muted-foreground">{hint}</p>
        </div>
        <Button variant="outline" size="sm" onClick={() => setEditing(true)}>
          Definir meta
        </Button>
      </div>
    );
  }

  if (editing) {
    return (
      <div className="space-y-2 rounded-lg border p-3">
        <p className="text-sm font-medium">{label}</p>
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">R$</span>
          <Input
            className="max-w-40"
            inputMode="decimal"
            placeholder="0,00"
            value={value}
            onChange={(event) => setValue(event.target.value)}
            autoFocus
          />
          <Button size="sm" onClick={save} disabled={setGoal.isPending}>
            Salvar
          </Button>
          <Button size="sm" variant="ghost" onClick={() => setEditing(false)}>
            Cancelar
          </Button>
        </div>
      </div>
    );
  }

  if (!goal) {
    return null;
  }

  const pct = Math.min(100, Math.round(goal.progress_pct));
  return (
    <div className="rounded-lg border p-3">
      <div className="mb-1 flex items-center justify-between gap-2">
        <div>
          <p className="text-sm font-medium">{label}</p>
          <p className="text-xs text-muted-foreground">
            {formatCents(goal.actual_cents)} de {formatCents(goal.target_cents)} ·{" "}
            <span className={goal.on_track ? "text-success" : "text-warning"}>
              {goal.on_track ? "no caminho" : "abaixo do ritmo"}
            </span>
          </p>
        </div>
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              setValue(centsToInput(goal.target_cents));
              setEditing(true);
            }}
          >
            Editar
          </Button>
          <Button
            variant="ghost"
            size="icon-sm"
            aria-label={`Remover meta de ${label}`}
            onClick={() => deleteGoal.mutate(metric)}
            disabled={deleteGoal.isPending}
          >
            <Trash2 />
          </Button>
        </div>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-muted">
        <div
          className={cn("h-full rounded-full", goal.on_track ? "bg-success" : "bg-primary")}
          style={{ width: `${pct}%` }}
        />
      </div>
      <p className="mt-1 text-xs text-muted-foreground">
        Projeção no fim do mês: {formatCents(goal.projected_cents)} ({goal.progress_pct}% da meta).
      </p>
    </div>
  );
}
