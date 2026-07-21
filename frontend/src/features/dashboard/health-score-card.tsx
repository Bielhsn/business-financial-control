import { HeartPulse } from "lucide-react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useHealthScore } from "@/features/dashboard/use-health";
import type { HealthRating, HealthScoreResponse } from "@/lib/api-types";
import { cn } from "@/lib/utils";

const RATING: Record<HealthRating, { label: string; text: string; ring: string }> = {
  excellent: { label: "Excelente", text: "text-success", ring: "text-success" },
  good: { label: "Bom", text: "text-success", ring: "text-success" },
  attention: { label: "Atenção", text: "text-warning", ring: "text-warning" },
  critical: { label: "Crítico", text: "text-destructive", ring: "text-destructive" },
};

export function HealthScoreCard({ companyId }: { companyId: string }) {
  const { data, isLoading } = useHealthScore(companyId);

  if (isLoading) {
    return <Skeleton className="h-56 w-full" />;
  }
  if (!data) {
    return null;
  }

  const rating = RATING[data.rating];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <HeartPulse className="size-4 text-primary" /> Saúde do negócio
        </CardTitle>
        <CardDescription>
          Índice ponderado (0–100) de margem, caixa, reembolsos, metas e integrações.
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-5 sm:flex-row sm:items-center">
        <Gauge score={data.score} ratingClass={rating.ring} label={rating.label} />
        <Factors data={data} />
      </CardContent>
    </Card>
  );
}

function Gauge({
  score,
  ratingClass,
  label,
}: {
  score: number;
  ratingClass: string;
  label: string;
}) {
  const radius = 42;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - score / 100);
  return (
    <div
      className="relative flex shrink-0 items-center justify-center"
      style={{ width: 112, height: 112 }}
    >
      <svg width={112} height={112} className="-rotate-90">
        <circle cx={56} cy={56} r={radius} fill="none" strokeWidth={8} className="stroke-muted" />
        <circle
          cx={56}
          cy={56}
          r={radius}
          fill="none"
          strokeWidth={8}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className={cn("stroke-current transition-all", ratingClass)}
        />
      </svg>
      <div className="absolute flex flex-col items-center">
        <span className="text-2xl font-bold tracking-tight">{score}</span>
        <span className={cn("text-xs font-medium", ratingClass)}>{label}</span>
      </div>
    </div>
  );
}

function Factors({ data }: { data: HealthScoreResponse }) {
  if (data.factors.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        Registre lançamentos, metas ou integrações para o índice ganhar precisão.
      </p>
    );
  }
  return (
    <div className="flex-1 space-y-2">
      {data.factors.map((factor) => (
        <div key={factor.key}>
          <div className="mb-0.5 flex items-center justify-between text-sm">
            <span>{factor.label}</span>
            <span className="tabular-nums text-muted-foreground">{factor.score}</span>
          </div>
          <div className="h-1.5 overflow-hidden rounded-full bg-muted">
            <div
              className={cn(
                "h-full rounded-full",
                factor.score >= 60
                  ? "bg-success"
                  : factor.score >= 40
                    ? "bg-warning"
                    : "bg-destructive",
              )}
              style={{ width: `${factor.score}%` }}
            />
          </div>
          <p className="mt-0.5 text-xs text-muted-foreground">{factor.detail}</p>
        </div>
      ))}
    </div>
  );
}
